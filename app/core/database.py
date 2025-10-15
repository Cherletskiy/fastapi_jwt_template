from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.logging_config import setup_logger
from app.core.config import settings


logger = setup_logger(__name__)


engine = create_async_engine(
    url=settings.DSN,
    echo=False,
    pool_size=5,
    max_overflow=10
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession
)


async def init_db():
    logger.info("Initializing database")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: conn.execute(text("SELECT 1")))
            logger.info("Database connection OK")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


async def close_db():
    await engine.dispose()
    logger.info("Database closed")