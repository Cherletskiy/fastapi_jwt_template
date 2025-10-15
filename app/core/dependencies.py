from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import AuthService
from app.core.logging_config import setup_logger
from app.services.user_service import UserService

logger = setup_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_async_session() -> AsyncSession:
    """Зависимость для получения асинхронной сессии в эндпоинтах.
    Пропускает HTTPException в случае ошибки, так как эти ошибки обрабатываются внутри сервиса.
    Остальные ошибки логируются, вызывается rollback и 500 клиенту.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except HTTPException as e:
            raise e
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in async session: {e}")
            raise
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    user = await AuthService.get_current_user(token, session, expected_type="access")
    return user



