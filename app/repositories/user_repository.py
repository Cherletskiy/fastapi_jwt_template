from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.exceptions import DatabaseException
from app.core.logging_config import setup_logger


logger = setup_logger(__name__)


class UserRepository:
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
        result = await session.execute(select(User).filter_by(id=user_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).filter_by(email=email))
        return result.scalars().first()

    @staticmethod
    async def create_user(
            session: AsyncSession,
            username: str,
            email: str,
            first_name: str,
            last_name: str,
            middle_name: str,
            hashed_password: str
    ) -> User:
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                hashed_password=hashed_password
            )

            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
        except IntegrityError as e:
            await session.rollback()
            raise DatabaseException(internal_detail=str(e))
