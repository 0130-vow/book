from abc import ABC, abstractmethod

from ..schemas import BookBrief, BookDetail, ChapterContent


class SourceProvider(ABC):
    identifier: str
    name: str
    base_url: str = ""

    @abstractmethod
    async def search(self, keyword: str) -> list[BookBrief]: ...

    @abstractmethod
    async def get_book_detail(self, book_id: str) -> BookDetail: ...

    @abstractmethod
    async def get_chapter_content(
        self, book_id: str, chapter_id: str
    ) -> ChapterContent: ...

