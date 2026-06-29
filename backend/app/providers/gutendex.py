import re
from collections.abc import Callable
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from ..schemas import BookBrief, BookDetail, ChapterBrief, ChapterContent
from .base import SourceProvider


class GutendexProvider(SourceProvider):
    identifier = "gutendex"
    name = "Project Gutenberg"
    base_url = "https://gutendex.com"

    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient,
    ):
        self.transport = transport
        self.client_factory = client_factory

    def _client(self) -> httpx.AsyncClient:
        return self.client_factory(
            transport=self.transport,
            timeout=7.0,
            follow_redirects=True,
            headers={
                "User-Agent": "BookHub/1.2 (+https://github.com/0130-vow/book)"
            },
        )

    @staticmethod
    def _author(payload: dict) -> str:
        return "、".join(item.get("name", "") for item in payload.get("authors", []))

    def _brief(self, payload: dict) -> BookBrief:
        formats = payload.get("formats", {})
        return BookBrief(
            external_id=str(payload["id"]),
            title=payload.get("title", "未命名"),
            author=self._author(payload),
            cover=formats.get("image/jpeg", ""),
            status="公版",
            words=None,
            updated_at=f"下载 {payload.get('download_count', 0)} 次",
            source=self.identifier,
            source_name=self.name,
        )

    async def _get_book(self, book_id: str) -> dict:
        try:
            async with self._client() as client:
                response = await client.get(f"{self.base_url}/books/{book_id}")
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="公版书源暂时不可用") from exc
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="未找到书籍")
        try:
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="公版书源响应异常") from exc

    async def search(self, keyword: str) -> list[BookBrief]:
        async with self._client() as client:
            response = await client.get(
                f"{self.base_url}/books",
                params={"search": keyword, "mime_type": "text/"},
            )
        response.raise_for_status()
        books = response.json().get("results", [])
        return [self._brief(book) for book in books[:12]]

    async def get_book_detail(self, book_id: str) -> BookDetail:
        payload = await self._get_book(book_id)
        brief = self._brief(payload)
        summaries = payload.get("summaries") or []
        subjects = payload.get("subjects") or []
        shelves = payload.get("bookshelves") or []
        return BookDetail(
            **brief.model_dump(),
            intro=(summaries[0] if summaries else "；".join(subjects[:3])),
            category=(shelves[0] if shelves else subjects[0] if subjects else "公版文学"),
            chapters=[ChapterBrief(id="full", index=0, title="全文")],
        )

    @staticmethod
    def _content_url(formats: dict) -> tuple[str, bool] | None:
        plain = [
            (key, value)
            for key, value in formats.items()
            if key.startswith("text/plain") and value
        ]
        plain.sort(key=lambda item: "utf-8" not in item[0])
        if plain:
            return plain[0][1], False
        html = next(
            (
                value
                for key, value in formats.items()
                if key.startswith("text/html") and value
            ),
            None,
        )
        return (html, True) if html else None

    @staticmethod
    def _clean_text(raw: str) -> str:
        start = re.search(
            r"\*{3}\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*{3}",
            raw,
            flags=re.IGNORECASE,
        )
        end = re.search(
            r"\*{3}\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK",
            raw,
            flags=re.IGNORECASE,
        )
        if end:
            raw = raw[: end.start()]
        if start:
            raw = raw[start.end() :]
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        raw = re.sub(r"\n{4,}", "\n\n\n", raw)
        return raw.strip()

    async def get_chapter_content(
        self, book_id: str, chapter_id: str
    ) -> ChapterContent:
        if chapter_id != "full":
            raise HTTPException(status_code=404, detail="未找到章节")
        payload = await self._get_book(book_id)
        selected = self._content_url(payload.get("formats", {}))
        if not selected:
            raise HTTPException(status_code=422, detail="该书没有可阅读的文本格式")
        url, is_html = selected
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            hostname == "gutenberg.org" or hostname.endswith(".gutenberg.org")
        ):
            raise HTTPException(status_code=422, detail="书籍正文地址不受信任")
        try:
            async with self._client() as client:
                response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="书籍正文下载失败") from exc
        raw = (
            BeautifulSoup(response.text, "html.parser").get_text("\n")
            if is_html
            else response.text
        )
        content = self._clean_text(raw)[:5_000_000]
        if not content:
            raise HTTPException(status_code=502, detail="书籍正文为空")
        return ChapterContent(
            id="full",
            index=0,
            title="全文",
            book_external_id=str(payload["id"]),
            content=content,
        )
