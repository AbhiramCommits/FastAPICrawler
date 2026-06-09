import os

import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "crawl_metadata.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS crawl_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    status_code INTEGER,
    title TEXT,
    word_count INTEGER,
    crawled_at TEXT,
    elapsed_ms REAL,
    batch_id TEXT,
    UNIQUE(url, batch_id)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_crawled_at ON crawl_results(crawled_at);
"""

INSERT_SQL = """
INSERT OR IGNORE INTO crawl_results
    (url, status_code, title, word_count, crawled_at, elapsed_ms, batch_id)
VALUES
    (:url, :status_code, :title, :word_count, :crawled_at, :elapsed_ms, :batch_id);
"""


async def init_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute(CREATE_TABLE_SQL)
    await db.execute(CREATE_INDEX_SQL)
    await db.commit()
    return db


async def insert_results(db: aiosqlite.Connection, results: list[dict], batch_id: str) -> int:
    rows = []
    for r in results:
        rows.append({
            "url": r["url"],
            "status_code": r.get("status_code", 0),
            "title": r.get("title", ""),
            "word_count": r.get("word_count", 0),
            "crawled_at": r.get("crawled_at", ""),
            "elapsed_ms": r.get("elapsed_ms", 0),
            "batch_id": batch_id,
        })

    cursor = await db.executemany(INSERT_SQL, rows)
    await db.commit()
    return cursor.rowcount


async def get_results(db: aiosqlite.Connection, limit: int = 100, offset: int = 0) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM crawl_results ORDER BY crawled_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_stats(db: aiosqlite.Connection) -> dict:
    cursor = await db.execute("""
        SELECT
            COUNT(*) AS total_urls,
            AVG(elapsed_ms) AS avg_elapsed_ms,
            SUM(CASE WHEN status_code >= 200 AND status_code < 400 THEN 1 ELSE 0 END) AS success_count,
            SUM(CASE WHEN status_code = 0 OR status_code >= 400 THEN 1 ELSE 0 END) AS error_count,
            MAX(crawled_at) AS last_crawled_at
        FROM crawl_results
    """)
    row = await cursor.fetchone()
    return {
        "total_urls": row["total_urls"],
        "avg_elapsed_ms": round(row["avg_elapsed_ms"], 2) if row["avg_elapsed_ms"] else 0,
        "success_count": row["success_count"],
        "error_count": row["error_count"],
        "last_crawled_at": row["last_crawled_at"] or "",
    }


async def get_batch(db: aiosqlite.Connection, batch_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM crawl_results WHERE batch_id = ? ORDER BY crawled_at DESC",
        (batch_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
