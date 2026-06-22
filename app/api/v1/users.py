from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_async_session, get_current_user
from app.services.user_service import UserService
from app.api.v1.schemas import UserResponse, UserUpdate
from app.models.user import User
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    logger.info(f"User accessed /me: {current_user.email}")
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(user_data: UserUpdate,
                    current_user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_async_session)):
    user = await UserService.update_user(session, current_user, user_data)
    return user


@router.delete("/deactivate")
async def deactivate_user(current_user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_async_session)):
    await UserService.deactivate_user(session, current_user)

    logger.info(f"User deactivated: {current_user.email}")
    return {"message": f"User {current_user.email} deactivated"}