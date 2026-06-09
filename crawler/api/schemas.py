from typing import Optional

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    urls: Optional[list[str]] = None
    batch_id: Optional[str] = None


class CrawlResponse(BaseModel):
    batch_id: str
    total_crawled: int
    success_count: int
    error_count: int
    avg_elapsed_ms: float


class CrawlResult(BaseModel):
    id: int
    url: str
    status_code: int
    title: str
    word_count: int
    crawled_at: str
    elapsed_ms: float
    batch_id: str


class ResultsResponse(BaseModel):
    results: list[CrawlResult]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_urls: int
    avg_elapsed_ms: float
    success_count: int
    error_count: int
    last_crawled_at: str


class HealthResponse(BaseModel):
    status: str
    db: str


class ErrorResponse(BaseModel):
    error: str
