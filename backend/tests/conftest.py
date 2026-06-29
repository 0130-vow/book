import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path: Path):
    os.environ["BOOKHUB_DATA_DIR"] = str(tmp_path)
    os.environ["BOOKHUB_TOKEN"] = "test-token"
    os.environ["BOOKHUB_AUTH_ENABLED"] = "true"

    from app.database import Base, engine
    from app.main import app
    from app.providers import providers

    async def offline_search(_keyword: str):
        return []

    providers["gutendex"].search = offline_search

    Base.metadata.drop_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)


@pytest.fixture()
def auth_headers():
    return {"X-BookHub-Token": "test-token"}
