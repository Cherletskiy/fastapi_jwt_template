from fastapi import APIRouter, Depends

from app.core.dependencies import require_roles_factory
from app.models.user import User
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/moderation")
async def moderation_dashboard(user: User = Depends(require_roles_factory(["moderator", "admin"]))):
    """Доступен только модераторам и админам"""
    logger.info(f"User ID {user.id} - {user.email} logged in moderation dashboard")
    return {
        "message": f"Добро пожаловать в панель модерации, {user.username}!",
        "user_id": user.id,
        "roles": [role.name for role in user.roles]
    }

@router.get("/admin_panel")
async def admin_panel(user: User = Depends(require_roles_factory(["admin"]))):
    """Доступен только админам"""
    logger.info(f"User ID {user.id} - {user.email} logged in admin panel")
    return {
        "message": f"Добро пожаловать в админ-панель, {user.username}!",
        "user_id": user.id,
        "roles": [role.name for role in user.roles]
    }