from datetime import datetime

import pytest_asyncio
from fastapi.testclient import TestClient
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.security import AuthService
from app.main import app
from app.models.base import Base


# Создаем клиент внутри фикстуры, а не глобально
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_async_session():
    """Mock асинхронной сессии"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password_123"
    user.first_name = "Ivan"
    user.last_name = "Petrov"
    user.middle_name = "Sergeevich"
    user.is_active = True
    user.created_at = datetime.utcnow()
    return user


@pytest.fixture
def valid_access_token(mock_user):
    return AuthService.create_access_token({"sub": str(mock_user.id)})


@pytest.fixture
def valid_refresh_token(mock_user):
    return AuthService.create_refresh_token({"sub": str(mock_user.id)})


TEST_DB_NAME = os.getenv("TEST_DB_NAME", "testdb")
TEST_DB_USER = os.getenv("TEST_DB_USER", "testuser")
TEST_DB_PWD = os.getenv("TEST_DB_PWD", "testpass")
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("TEST_DB_PORT", "5433")

# TEST_DSN = f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PWD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
TEST_DSN = f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PWD}@localhost:5433/{TEST_DB_NAME}"

@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(TEST_DSN, echo=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Очистка и создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Создаем новую сессию для каждого теста
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

# Глобальная конфигурация pytest
pytest_plugins = ["pytest_asyncio"]
