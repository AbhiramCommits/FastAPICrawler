import asyncio
import time
from typing import Optional

import httpx
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; FastAPICrawler/1.0; "
        "+https://github.com/anomalyco/fastapicrawler)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


class AsyncCrawler:
    def __init__(self, seed_urls: list[str], max_concurrency: int = 10):
        self.seed_urls = seed_urls
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch(
        self, url: str, client: Optional[httpx.AsyncClient] = None
    ) -> tuple[str, int, Optional[str], float]:
        own_client = client is None
        if own_client:
            client = httpx.AsyncClient(
                timeout=10.0, follow_redirects=True, headers=DEFAULT_HEADERS
            )

        try:
            start = time.monotonic()
            async with self._semaphore:
                response = await client.get(url)
            elapsed = (time.monotonic() - start) * 1000
            return (url, response.status_code, response.text, elapsed)
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000 if 'start' in dir() else 0
            return (url, 0, None, elapsed_ms)
        finally:
            if own_client:
                await client.aclose()

    async def crawl_all(self, urls: Optional[list[str]] = None) -> list[dict]:
        if urls is None:
            urls = self.seed_urls

        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers=DEFAULT_HEADERS
        ) as client:
            tasks = [self._crawl_one(client, url) for url in urls]
            results = await asyncio.gather(*tasks)

        return results

    async def _crawl_one(
        self, client: httpx.AsyncClient, url: str
    ) -> dict:
        start = time.monotonic()
        try:
            async with self._semaphore:
                response = await client.get(url)
            elapsed_ms = (time.monotonic() - start) * 1000
            html = response.text

            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            body = soup.find("body")
            body_text = body.get_text(separator=" ", strip=True) if body else ""
            word_count = len(body_text.split()) if body_text else 0

            return {
                "url": url,
                "status_code": response.status_code,
                "title": title,
                "word_count": word_count,
                "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "elapsed_ms": round(elapsed_ms, 2),
            }
        except Exception:
            elapsed_ms = (time.monotonic() - start) * 1000
            return {
                "url": url,
                "status_code": 0,
                "title": "",
                "word_count": 0,
                "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "elapsed_ms": round(elapsed_ms, 2),
            }
