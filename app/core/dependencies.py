from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import AuthService
from app.core.exceptions import DatabaseException, AppException
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_async_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        except AppException as e:
            if isinstance(e, DatabaseException):
                await session.rollback()
                logger.error(f"Database error in session: {e.internal_detail}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error in async session: {e}")
            raise
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    user = await AuthService.get_current_user(token, session, expected_type="access")
    return user


async def get_refresh_token(refresh_token: str | None = Cookie(default=None)):
    if refresh_token is None:
        logger.warning("No refresh_token in cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided"
        )
    logger.debug(f"Extracted refresh_token from cookie: {refresh_token}")
    return refresh_token
