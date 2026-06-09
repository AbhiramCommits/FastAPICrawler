import pytest

from crawler.core.crawler import AsyncCrawler


@pytest.mark.asyncio
async def test_fetch_returns_dict(mock_async_client):
    crawler = AsyncCrawler(["https://example.com"])
    results = await crawler.crawl_all()
    assert len(results) == 1
    result = results[0]
    assert "url" in result
    assert "status_code" in result
    assert "title" in result
    assert "word_count" in result
    assert result["url"] == "https://example.com"
    assert result["status_code"] == 200
    assert result["title"] == "Test"
    assert result["word_count"] == 2


@pytest.mark.asyncio
async def test_crawl_all_respects_concurrency(mock_async_client):
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3",
        "https://example.com/4",
        "https://example.com/5",
    ]
    crawler = AsyncCrawler(urls)
    results = await crawler.crawl_all()
    assert len(results) == 5
    for result in results:
        assert result["status_code"] == 200
        assert result["title"] == "Test"
