from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)


class UserService:
    @staticmethod
    async def authenticate_user(
        session: AsyncSession, email: str, password: str
    ) -> User | None:
        user = await UserRepository.get_user_by_email(session, email)
        if not user or not AuthService.verify_password(password, user.hashed_password):
            logger.warning(f"Invalid login attempt: {email}")
            raise InvalidCredentialsException()
        return user


    @staticmethod
    async def create_user(
        session: AsyncSession, username: str, email: str, hashed_password: str
    ) -> User:
        existing_user = await UserRepository.get_user_by_email(session, email)
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {email}")
            raise UserAlreadyExistsException(detail=f"Email {email} already registered")

        user = await UserRepository.create_user(
            session, username, email, hashed_password
        )
        logger.info(f"User created: {email}")
        return user

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> User:
        user = await UserRepository.get_user_by_email(session, email)
        return user
