from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import UserRole
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

    @staticmethod
    async def assign_role_to_user(session: AsyncSession, user_id: int, role_name: str) -> bool:
        """Назначает роль пользователю"""
        role = await AuthorizationRepository.get_role_by_name(session, role_name)
        if not role:
            logger.error(f"Role not found: {role_name}")
            return False

        # Проверяем нет ли уже такой роли у пользователя
        existing_link = await AuthorizationRepository.get_user_role_link(session, user_id, role.id)
        if existing_link:
            logger.info(f"User {user_id} already has role {role_name}")
            return True

        # Создаем связь
        await AuthorizationRepository.create_user_role(session, user_id, role.id)
        logger.info(f"Role {role_name} assigned to user {user_id}")
        return True