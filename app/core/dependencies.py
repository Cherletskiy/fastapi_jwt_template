from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.security import AuthService
from app.services.authorization_service import AuthorizationService
from app.core.exceptions import DatabaseException, AppException, UserIsInActive, InsufficientPermissionsException
from app.core.logging_config import setup_logger
from app.models.user import User

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
) -> User:
    user = await AuthService.get_current_user(token, session, expected_type="access")
    if not user.is_active:
        logger.warning(f"Inactive user attempted to authenticate: {user.id}")
        raise UserIsInActive()
    return user


async def get_refresh_token(refresh_token: str | None = Cookie(default=None)):
    if refresh_token is None:
        logger.warning("No refresh_token in cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )
    return refresh_token


def require_roles_factory(roles: list[str], all_required: bool = False):
    """
    Фабрика зависимостей для проверки ролей пользователя.
    """
    async def require_roles(
            current_user: User = Depends(get_current_user),
            session: AsyncSession = Depends(get_async_session),
    ) -> User:
        user_roles = await AuthorizationService.get_user_role_names(session, current_user.id)

        if all_required:
            if not all(role in user_roles for role in roles):
                raise InsufficientPermissionsException()
        else:
            if not any(role in user_roles for role in roles):
                raise InsufficientPermissionsException()

        requirement_type = "all" if all_required else "any of"
        logger.info(f"User {current_user.id} has {requirement_type} required roles: {roles}")
        return current_user
    return require_roles


# def require_permissions_factory(permissions: list[str], all_required: bool = False):
#     async def require_permissions(
#         current_user: User = Depends(get_current_user),
#         session: AsyncSession = Depends(get_async_session),
#     ) -> User:
#         user_perms = await AuthorizationService.has_permission_list(session, current_user.id)
#
#         if all_required:
#             if not all(perm in user_perms for perm in permissions):
#                 raise InsufficientPermissionsException()
#         else:
#             if not any(perm in user_perms for perm in permissions):
#                 raise InsufficientPermissionsException()
#
#         requirement_type = "all" if all_required else "any of"
#         logger.debug(f"User {current_user.id} has {requirement_type} required permissions: {permissions}")
#         return current_user
#     return require_permissions