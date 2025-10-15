from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import init_db, close_db
from app.core.migrations import run_migrations
from app.api.v1.auth import router as auth_router
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("Starting app")
    try:
        await run_migrations()
        await init_db()
        yield
    except Exception as e:
        logger.error(f"Error in lifespan: {e}")
    finally:
        logger.info("Stopping app")
        await close_db()


app = FastAPI(
    title="title",
    description="description",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(auth_router, prefix="/api/v1")
