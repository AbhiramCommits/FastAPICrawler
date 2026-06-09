import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from crawler.api.main import app
from crawler.db.database import init_db


@pytest_asyncio.fixture
async def async_client(monkeypatch):
    monkeypatch.setattr("crawler.db.database.DB_PATH", ":memory:")

    db = await init_db()
    app.state.db = db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await db.close()


@pytest.mark.asyncio
async def test_health_ok(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_stats_returns_dict(async_client):
    response = await async_client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_urls" in data
    assert data["total_urls"] == 0


@pytest.mark.asyncio
async def test_results_pagination(async_client):
    response = await async_client.get("/results", params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["results"], list)
    assert data["limit"] == 10
    assert data["offset"] == 0
