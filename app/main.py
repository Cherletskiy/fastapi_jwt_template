from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.database import init_db, close_db
from app.core.migrations import run_migrations
from app.api.v1.auth import router as auth_router
from app.core.exceptions import AppException, DatabaseException
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
    title="title", description="description", version="1.0.0", lifespan=lifespan
)


app.include_router(auth_router, prefix="/api/v1")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    log_message = f"Error at {request.url}: {exc.detail}"
    if isinstance(exc, DatabaseException):
        log_message += f"| Internal: {exc.internal_detail}"
    logger.error(log_message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error at {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again later."}
    )