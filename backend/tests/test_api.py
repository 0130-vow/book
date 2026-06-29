def test_health_does_not_require_auth(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_requires_token(client):
    assert client.get("/api/sources").status_code == 401


def test_search_detail_and_reading_flow(client, auth_headers):
    results = client.get(
        "/api/search", params={"keyword": "三国"}, headers=auth_headers
    )
    assert results.status_code == 200
    book = results.json()[0]

    detail = client.get(
        f"/api/catalog/{book['source']}/{book['external_id']}",
        headers=auth_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["chapters"]

    shelf = client.post(
        "/api/bookshelf",
        headers=auth_headers,
        json={
            "external_id": book["external_id"],
            "title": book["title"],
            "author": book["author"],
            "cover": book["cover"],
            "source": book["source"],
        },
    )
    assert shelf.status_code == 200
    shelf_id = shelf.json()["id"]

    chapter = client.get(
        f"/api/catalog/{book['source']}/{book['external_id']}/chapters/0",
        params={"bookshelf_id": shelf_id},
        headers=auth_headers,
    )
    assert chapter.status_code == 200
    assert len(chapter.json()["content"]) > 100

    progress = client.post(
        "/api/progress",
        headers=auth_headers,
        json={
            "book_id": shelf_id,
            "source": book["source"],
            "chapter_id": "0",
            "chapter_index": 0,
            "position": 0.35,
            "mode": "scroll",
        },
    )
    assert progress.status_code == 200
    assert progress.json()["position"] == 0.35


def test_download_book(client, auth_headers):
    shelf = client.post(
        "/api/bookshelf",
        headers=auth_headers,
        json={
            "external_id": "xiyou",
            "title": "西游记",
            "author": "吴承恩",
            "source": "classics-a",
        },
    ).json()
    response = client.post(f"/api/download/{shelf['id']}", headers=auth_headers)
    assert response.status_code == 200
    status = client.get(
        f"/api/download/{shelf['id']}/status", headers=auth_headers
    ).json()
    assert status["status"] == "completed"
    assert status["completed"] == status["total"] == 3
