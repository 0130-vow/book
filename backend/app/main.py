import asyncio
import json
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Bookshelf, Chapter, DownloadJob, SearchCache, Source, utcnow
from .providers import providers
from .schemas import (
    BookBrief,
    BookDetail,
    BookshelfCreate,
    BookshelfOut,
    BookshelfPatch,
    ChapterBrief,
    ChapterContent,
    DownloadOut,
    ProgressIn,
    SourceOut,
    SourcePatch,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for provider in providers.values():
            existing = db.scalar(
                select(Source).where(Source.identifier == provider.identifier)
            )
            if not existing:
                db.add(
                    Source(
                        name=provider.name,
                        identifier=provider.identifier,
                        base_url=provider.base_url,
                    )
                )
        interrupted = list(
            db.scalars(
                select(DownloadJob).where(
                    DownloadJob.status.in_(["queued", "downloading"])
                )
            )
        )
        for job in interrupted:
            job.status = "failed"
            job.error = "服务曾重启，请点击重试"
            job.updated_at = utcnow()
        db.commit()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    lifespan=lifespan,
    docs_url=None if settings.auth_enabled else "/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def token_auth(request: Request, call_next):
    if (
        settings.auth_enabled
        and request.url.path.startswith("/api")
        and request.url.path != "/api/health"
    ):
        supplied = request.headers.get("X-BookHub-Token", "")
        if not secrets.compare_digest(supplied, settings.token):
            return JSONResponse(status_code=401, content={"detail": "Token 无效"})
    return await call_next(request)


def get_provider(source: str):
    provider = providers.get(source)
    if not provider:
        raise HTTPException(status_code=404, detail="未知书源")
    return provider


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": "1.1.0"}


@app.get("/api/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(Source).order_by(Source.id)))


@app.patch("/api/sources/{identifier}", response_model=SourceOut)
def patch_source(
    identifier: str, payload: SourcePatch, db: Session = Depends(get_db)
):
    item = db.scalar(select(Source).where(Source.identifier == identifier))
    if not item:
        raise HTTPException(status_code=404, detail="未知书源")
    item.enabled = payload.enabled
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/search", response_model=list[BookBrief])
async def search_books(
    keyword: str = Query(min_length=1, max_length=100),
    source: str | None = None,
    db: Session = Depends(get_db),
):
    normalized = keyword.strip().lower()
    source_rows = {
        item.identifier: item for item in db.scalars(select(Source).order_by(Source.id))
    }
    if source:
        row = source_rows.get(source)
        if not row:
            raise HTTPException(status_code=404, detail="未知书源")
        if not row.enabled:
            raise HTTPException(status_code=409, detail="书源已停用")
        selected = [get_provider(source)]
        enabled_signature = source
    else:
        enabled_ids = [
            identifier
            for identifier, row in source_rows.items()
            if row.enabled and identifier in providers
        ]
        selected = [providers[identifier] for identifier in enabled_ids]
        enabled_signature = ",".join(sorted(enabled_ids))

    cache_key = f"{enabled_signature}:{normalized}"
    cached = db.scalar(select(SearchCache).where(SearchCache.cache_key == cache_key))
    now = datetime.now(timezone.utc)
    if cached:
        expires = cached.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires > now:
            return [BookBrief.model_validate(item) for item in json.loads(cached.payload)]

    async def safe_search(provider):
        try:
            results = await asyncio.wait_for(
                provider.search(normalized), timeout=settings.source_timeout
            )
            return provider.identifier, results, True
        except Exception:
            return provider.identifier, [], False

    batches = await asyncio.gather(*(safe_search(provider) for provider in selected))
    results = [item for _, batch, _ in batches for item in batch]
    for identifier, _, healthy in batches:
        row = source_rows.get(identifier)
        if row:
            row.healthy = healthy
    payload = json.dumps([item.model_dump() for item in results], ensure_ascii=False)
    if cached:
        cached.payload = payload
        cached.expires_at = now + timedelta(seconds=settings.search_cache_ttl)
    else:
        db.add(
            SearchCache(
                cache_key=cache_key,
                payload=payload,
                expires_at=now + timedelta(seconds=settings.search_cache_ttl),
            )
        )
    db.commit()
    return results


@app.get("/api/catalog/{source}/{book_id}", response_model=BookDetail)
async def book_detail(source: str, book_id: str):
    return await get_provider(source).get_book_detail(book_id)


@app.get(
    "/api/catalog/{source}/{book_id}/chapters", response_model=list[ChapterBrief]
)
async def chapter_list(source: str, book_id: str):
    return (await get_provider(source).get_book_detail(book_id)).chapters


@app.get(
    "/api/catalog/{source}/{book_id}/chapters/{chapter_id}",
    response_model=ChapterContent,
)
async def chapter_content(
    source: str,
    book_id: str,
    chapter_id: str,
    bookshelf_id: int | None = None,
    db: Session = Depends(get_db),
):
    if bookshelf_id:
        cached = db.scalar(
            select(Chapter).where(
                Chapter.book_id == bookshelf_id,
                Chapter.source == source,
                Chapter.external_chapter_id == chapter_id,
            )
        )
        if cached and cached.content:
            return ChapterContent(
                id=cached.external_chapter_id,
                index=cached.chapter_index,
                title=cached.chapter_name,
                book_external_id=book_id,
                content=cached.content,
            )
    content = await get_provider(source).get_chapter_content(book_id, chapter_id)
    if bookshelf_id:
        shelf = db.get(Bookshelf, bookshelf_id)
        if shelf:
            db.add(
                Chapter(
                    book_id=bookshelf_id,
                    source=source,
                    external_chapter_id=chapter_id,
                    chapter_index=content.index,
                    chapter_name=content.title,
                    content=content.content,
                )
            )
            try:
                db.commit()
            except Exception:
                db.rollback()
    return content


@app.get("/api/bookshelf", response_model=list[BookshelfOut])
def bookshelf(
    status: str | None = None,
    sort: str = "recent",
    db: Session = Depends(get_db),
):
    query = select(Bookshelf)
    if status:
        query = query.where(Bookshelf.display_status == status)
    order = (
        Bookshelf.title.asc()
        if sort == "title"
        else Bookshelf.created_at.desc()
        if sort == "created"
        else Bookshelf.last_read_at.desc().nullslast()
    )
    return list(db.scalars(query.order_by(order, Bookshelf.updated_at.desc())))


@app.post("/api/bookshelf", response_model=BookshelfOut)
def add_to_bookshelf(payload: BookshelfCreate, db: Session = Depends(get_db)):
    existing = db.scalar(
        select(Bookshelf).where(
            Bookshelf.external_id == payload.external_id,
            Bookshelf.current_source == payload.source,
        )
    )
    if existing:
        return existing
    book = Bookshelf(
        external_id=payload.external_id,
        title=payload.title,
        author=payload.author,
        cover=payload.cover,
        intro=payload.intro,
        category=payload.category,
        status=payload.status,
        current_source=payload.source,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@app.patch("/api/bookshelf/{book_id}", response_model=BookshelfOut)
def patch_bookshelf(
    book_id: int, payload: BookshelfPatch, db: Session = Depends(get_db)
):
    book = db.get(Bookshelf, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书架中没有这本书")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(book, key, value)
    book.updated_at = utcnow()
    db.commit()
    db.refresh(book)
    return book


@app.delete("/api/bookshelf/{book_id}", status_code=204)
def remove_from_bookshelf(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Bookshelf, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书架中没有这本书")
    db.execute(delete(DownloadJob).where(DownloadJob.book_id == book_id))
    db.execute(delete(Chapter).where(Chapter.book_id == book_id))
    db.delete(book)
    db.commit()


@app.get("/api/progress/{book_id}")
def get_progress(book_id: int, source: str, db: Session = Depends(get_db)):
    book = db.get(Bookshelf, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书架中没有这本书")
    return json.loads(book.source_data or "{}").get(source, {})


@app.post("/api/progress")
def save_progress(payload: ProgressIn, db: Session = Depends(get_db)):
    book = db.get(Bookshelf, payload.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="请先加入书架")
    data = json.loads(book.source_data or "{}")
    data[payload.source] = {
        **payload.model_dump(exclude={"book_id", "source"}),
        "progress": min(
            1,
            (payload.chapter_index + payload.position) / payload.total_chapters,
        ),
        "updated_at": utcnow().isoformat(),
    }
    book.source_data = json.dumps(data, ensure_ascii=False)
    book.last_read_at = utcnow()
    book.updated_at = utcnow()
    db.commit()
    return data[payload.source]


async def cache_book(job_id: int, book_id: int) -> None:
    with SessionLocal() as db:
        job = db.get(DownloadJob, job_id)
        book = db.get(Bookshelf, book_id)
        if not job or not book:
            return
        job.status = "downloading"
        job.error = ""
        db.commit()

        try:
            provider = get_provider(book.current_source)
            detail = await provider.get_book_detail(book.external_id)
            job.total = len(detail.chapters)
            db.commit()
            for chapter in detail.chapters:
                cached = db.scalar(
                    select(Chapter).where(
                        Chapter.book_id == book.id,
                        Chapter.source == book.current_source,
                        Chapter.external_chapter_id == chapter.id,
                    )
                )
                if not cached:
                    content = await provider.get_chapter_content(
                        book.external_id, chapter.id
                    )
                    db.add(
                        Chapter(
                            book_id=book.id,
                            source=book.current_source,
                            external_chapter_id=chapter.id,
                            chapter_index=content.index,
                            chapter_name=content.title,
                            content=content.content,
                        )
                    )
                job.completed = chapter.index + 1
                job.updated_at = utcnow()
                db.commit()
                await asyncio.sleep(0.5)
            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)[:500]
        job.updated_at = utcnow()
        db.commit()


@app.get("/api/download", response_model=list[DownloadOut])
def list_downloads(db: Session = Depends(get_db)):
    return list(db.scalars(select(DownloadJob).order_by(DownloadJob.updated_at.desc())))


@app.post("/api/download/{book_id}", response_model=DownloadOut)
def start_download(
    book_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    book = db.get(Bookshelf, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="请先加入书架")
    job = db.scalar(select(DownloadJob).where(DownloadJob.book_id == book_id))
    if not job:
        job = DownloadJob(book_id=book_id)
        db.add(job)
    elif job.status == "downloading":
        return job
    else:
        job.status = "queued"
        job.completed = 0
        job.total = 0
        job.error = ""
        job.updated_at = utcnow()
    db.commit()
    db.refresh(job)
    background_tasks.add_task(cache_book, job.id, book_id)
    return job


@app.get("/api/download/{book_id}/status", response_model=DownloadOut)
def download_status(book_id: int, db: Session = Depends(get_db)):
    job = db.scalar(select(DownloadJob).where(DownloadJob.book_id == book_id))
    if not job:
        raise HTTPException(status_code=404, detail="没有下载任务")
    return job
