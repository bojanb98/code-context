import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger

from .routes import index, search

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        f"Core library version: {__import__('core').__version__ if hasattr(__import__('core'), '__version__') else 'unknown'}"
    )
    logger.info("Context service initialized successfully")

    yield

    logger.info("Shutting down Code Context API")


app = FastAPI(
    title="Code Context API",
    description="REST API for semantic code search and indexing using Qdrant and FastEmbed",
    version="0.1.0",
    docs_url="/swagger",
    openapi_url="/openapi",
    lifespan=lifespan,
)

app.include_router(index.router, prefix="/api/index", tags=["indexing"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail=exc)
