from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.models.rbac import Role, Permission, UserRole, RolePermission
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)


class AuthorizationRepository:
    @staticmethod
    async def get_user_roles(session: AsyncSession, user_id: int) -> List[Role]:
        """Все роли пользователя (объекты Role)."""
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


    @staticmethod
    async def get_user_permissions(session: AsyncSession, user_id: int) -> List[Permission]:
        """Все разрешения пользователя (объекты Permission)."""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


    @staticmethod
    async def get_user_permission_names(session: AsyncSession, user_id: int) -> List[str]:
        """Список имён разрешений пользователя."""
        perms = await AuthorizationRepository.get_user_permissions(session, user_id)
        return [p.name for p in perms]


    @staticmethod
    async def get_role_by_name(session: AsyncSession, name: str) -> Role | None:
        result = await session.execute(select(Role).filter_by(name=name))
        return result.scalars().first()

    @staticmethod
    async def get_permission_by_name(session: AsyncSession, name: str) -> Permission | None:
        result = await session.execute(select(Permission).filter_by(name=name))
        return result.scalars().first()