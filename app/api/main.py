import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.models.transaction import Base
from app.api.routes import transactions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Creates database tables on startup if they don't exist.
    """
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield
    await engine.dispose()
    logger.info("Database connection closed")


app = FastAPI(
    title="Portal Transaction Monitor",
    description="Monitors business registry transactions via web scraping and API verification",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {"status": "ok"}