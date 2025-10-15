from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
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
        session: AsyncSession, username: str, email: str, hashed_password: str
    ) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
