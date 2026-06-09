from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from crawler.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.db = await init_db()
    yield
    await app.state.db.close()


app = FastAPI(title="FastAPICrawler", lifespan=lifespan)
