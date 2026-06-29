import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.providers.gutendex import GutendexProvider


BOOK = {
    "id": 1342,
    "title": "Pride and Prejudice",
    "authors": [{"name": "Austen, Jane"}],
    "subjects": ["Courtship -- Fiction"],
    "summaries": ["A classic novel of manners."],
    "bookshelves": ["Best Books Ever Listings"],
    "formats": {
        "image/jpeg": "https://example.test/cover.jpg",
        "text/plain; charset=utf-8": "https://www.gutenberg.org/book.txt",
    },
    "download_count": 100,
}


def transport(request: httpx.Request) -> httpx.Response:
    if request.url.host == "www.gutenberg.org":
        return httpx.Response(
            200,
            text=(
                "*** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***\n"
                "It is a truth universally acknowledged.\n"
                "*** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***"
            ),
        )
    if request.url.path == "/books/1342":
        return httpx.Response(200, json=BOOK)
    if request.url.path == "/books/9":
        payload = {**BOOK, "id": 9, "formats": {"text/plain": "https://evil.test/book.txt"}}
        return httpx.Response(200, json=payload)
    return httpx.Response(200, json={"results": [BOOK]})


def test_gutendex_search_detail_and_content():
    provider = GutendexProvider(transport=httpx.MockTransport(transport))

    results = asyncio.run(provider.search("pride"))
    assert results[0].title == "Pride and Prejudice"
    assert results[0].source == "gutendex"

    detail = asyncio.run(provider.get_book_detail("1342"))
    assert detail.chapters[0].id == "full"
    assert detail.category == "Best Books Ever Listings"

    content = asyncio.run(provider.get_chapter_content("1342", "full"))
    assert content.content == "It is a truth universally acknowledged."


def test_gutendex_rejects_untrusted_content_host():
    provider = GutendexProvider(transport=httpx.MockTransport(transport))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(provider.get_chapter_content("9", "full"))
    assert exc.value.status_code == 422
