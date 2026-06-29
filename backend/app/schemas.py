from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BookBrief(BaseModel):
    external_id: str
    title: str
    author: str = ""
    cover: str = ""
    status: str = ""
    words: int | None = None
    updated_at: str = ""
    source: str
    source_name: str


class ChapterBrief(BaseModel):
    id: str
    index: int
    title: str


class BookDetail(BookBrief):
    intro: str = ""
    category: str = ""
    chapters: list[ChapterBrief] = []


class ChapterContent(ChapterBrief):
    book_external_id: str
    content: str


class SourceOut(BaseModel):
    identifier: str
    name: str
    enabled: bool
    healthy: bool


class DownloadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    status: str
    completed: int
    total: int
    error: str
    created_at: datetime
    updated_at: datetime


class BookshelfCreate(BaseModel):
    external_id: str
    title: str
    author: str = ""
    cover: str = ""
    intro: str = ""
    category: str = ""
    status: str = ""
    source: str


class BookshelfPatch(BaseModel):
    display_status: Literal["reading", "finished", "archived"] | None = None
    current_source: str | None = None


class BookshelfOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    title: str
    author: str
    cover: str
    intro: str
    category: str
    status: str
    current_source: str
    source_data: str
    display_status: str
    last_read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProgressIn(BaseModel):
    book_id: int
    source: str
    chapter_id: str
    chapter_index: int = Field(ge=0)
    position: float = Field(default=0, ge=0, le=1)
    mode: Literal["scroll", "page"] = "scroll"


class ProgressOut(ProgressIn):
    progress: float = 0
    updated_at: datetime
