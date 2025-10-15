from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import AuthService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)


class UserService:
    @staticmethod
    async def authenticate_user(
        session: AsyncSession, email: str, password: str
    ) -> User | None:
        user = await UserRepository.get_user_by_email(session, email)
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {email}")
            return None
        return user

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
        user = await UserRepository.get_user_by_id(session, user_id)
        if not user:
            logger.warning(f"User with id {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    @staticmethod
    async def create_user(
        session: AsyncSession, username: str, email: str, hashed_password: str
    ) -> User:
        user = await UserRepository.create_user(
            session, username, email, hashed_password
        )
        logger.info(f"User created: {email}")
        return user

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> User:
        user = await UserRepository.get_user_by_email(session, email)
        return user
