from datetime import datetime
from fastapi.testclient import TestClient
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthService
from app.models.user import User
from app.main import app


client = TestClient(app)

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
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

# Глобальная конфигурация pytest
pytest_plugins = ["pytest_asyncio"]
