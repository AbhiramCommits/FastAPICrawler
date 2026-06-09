# FastAPICrawler

An asynchronous web crawler built with FastAPI, httpx, and BeautifulSoup.

## Structure

```
crawler/
  core/     - Core crawling engine (AsyncCrawler, seed URLs)
  api/      - FastAPI application and routes
  db/       - Database layer (aiosqlite)
  tests/    - Test suite (pytest + pytest-asyncio)
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from crawler.core.crawler import AsyncCrawler
from crawler.core.targets import SEED_URLS

async def main():
    crawler = AsyncCrawler(SEED_URLS, max_concurrency=10)
    results = await crawler.crawl_all()
    for r in results:
        print(r["url"], r["status_code"], r["title"])

import asyncio
asyncio.run(main())
```
