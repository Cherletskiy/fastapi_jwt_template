from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.rbac_repository import AuthorizationRepository
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


class AuthorizationService:
    """Сервис только для проверки доступа."""

    @staticmethod
    async def has_permission(session: AsyncSession, user_id: int, permission_name: str) -> bool:
        """Проверяет, есть ли разрешение у пользователя."""
        permission_names = await AuthorizationRepository.get_user_permission_names(session, user_id)
        return permission_name in permission_names

    @staticmethod
    async def has_permission_list(session: AsyncSession, user_id: int) -> list[str]:
        """Возвращает все разрешения пользователя (имена)."""
        return await AuthorizationRepository.get_user_permission_names(session, user_id)

    @staticmethod
    async def get_user_role_names(session: AsyncSession, user_id: int) -> list[str]:
        """Возвращает все роли пользователя (имена)."""
        roles = await AuthorizationRepository.get_user_roles(session, user_id)
        return [role.name for role in roles]