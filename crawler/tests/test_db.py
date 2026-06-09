import pytest

from crawler.db.database import count_results, get_results, get_stats, init_db, insert_results


@pytest.fixture(autouse=True)
def override_db_path(monkeypatch):
    monkeypatch.setattr("crawler.db.database.DB_PATH", ":memory:")


@pytest.mark.asyncio
async def test_insert_and_get():
    db = await init_db()
    batch_id = "batch-001"

    results = [
        {"url": "https://a.com", "status_code": 200, "title": "A", "word_count": 10, "crawled_at": "2025-01-01T00:00:00Z", "elapsed_ms": 50.0},
        {"url": "https://b.com", "status_code": 404, "title": "B", "word_count": 20, "crawled_at": "2025-01-01T00:00:01Z", "elapsed_ms": 30.0},
        {"url": "https://c.com", "status_code": 200, "title": "C", "word_count": 30, "crawled_at": "2025-01-01T00:00:02Z", "elapsed_ms": 40.0},
    ]
    await insert_results(db, results, batch_id)

    rows = await get_results(db)
    assert len(rows) == 3
    assert rows[0]["url"] == "https://c.com"

    total = await count_results(db)
    assert total == 3

    await db.close()


@pytest.mark.asyncio
async def test_stats_after_insert():
    db = await init_db()
    batch_id = "batch-002"

    results = [
        {"url": "https://ok.com", "status_code": 200, "title": "OK", "word_count": 10, "crawled_at": "2025-01-01T00:00:00Z", "elapsed_ms": 50.0},
        {"url": "https://err.com", "status_code": 500, "title": "Err", "word_count": 0, "crawled_at": "2025-01-01T00:00:01Z", "elapsed_ms": 25.0},
        {"url": "https://fail.com", "status_code": 0, "title": "", "word_count": 0, "crawled_at": "2025-01-01T00:00:02Z", "elapsed_ms": 0.0},
        {"url": "https://also-ok.com", "status_code": 301, "title": "Redirect", "word_count": 5, "crawled_at": "2025-01-01T00:00:03Z", "elapsed_ms": 10.0},
    ]
    await insert_results(db, results, batch_id)

    stats = await get_stats(db)
    assert stats["total_urls"] == 4
    assert stats["success_count"] == 2
    assert stats["error_count"] == 2
    assert stats["avg_elapsed_ms"] > 0

    await db.close()
