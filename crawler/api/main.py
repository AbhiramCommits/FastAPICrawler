import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from crawler.api.schemas import (
    CrawlRequest,
    CrawlResponse,
    CrawlResult,
    ErrorResponse,
    HealthResponse,
    ResultsResponse,
    StatsResponse,
)
from crawler.core.crawler import AsyncCrawler
from crawler.core.targets import SEED_URLS
from crawler.db.database import (
    count_results,
    get_batch,
    get_results,
    get_stats,
    init_db,
    insert_results,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.db = await init_db()
    yield
    await app.state.db.close()


app = FastAPI(title="FastAPICrawler", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500, content=ErrorResponse(error=str(exc)).model_dump()
    )


@app.post("/crawl", response_model=CrawlResponse)
async def crawl(req: Request, body: CrawlRequest) -> CrawlResponse:
    urls = body.urls if body.urls is not None else SEED_URLS
    batch_id = body.batch_id if body.batch_id else uuid.uuid4().hex[:8]

    crawler = AsyncCrawler(urls)
    results = await crawler.crawl_all()

    await insert_results(req.app.state.db, results, batch_id)

    elapsed_values = [r["elapsed_ms"] for r in results]
    avg_elapsed = sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0

    success = sum(1 for r in results if 200 <= r["status_code"] < 400)
    errors = len(results) - success

    return CrawlResponse(
        batch_id=batch_id,
        total_crawled=len(results),
        success_count=success,
        error_count=errors,
        avg_elapsed_ms=round(avg_elapsed, 2),
    )


@app.get("/results", response_model=ResultsResponse)
async def list_results(
    req: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ResultsResponse:
    rows = await get_results(req.app.state.db, limit=limit, offset=offset)
    total = await count_results(req.app.state.db)
    return ResultsResponse(
        results=[CrawlResult(**row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/results/{batch_id}", response_model=list[CrawlResult])
async def list_batch_results(req: Request, batch_id: str) -> list[CrawlResult]:
    rows = await get_batch(req.app.state.db, batch_id)
    return [CrawlResult(**row) for row in rows]


@app.get("/stats", response_model=StatsResponse)
async def stats(req: Request) -> StatsResponse:
    data = await get_stats(req.app.state.db)
    return StatsResponse(**data)


@app.get("/health", response_model=HealthResponse)
async def health(req: Request) -> HealthResponse:
    db_status = "disconnected"
    try:
        await req.app.state.db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        pass
    return HealthResponse(status="ok", db=db_status)
