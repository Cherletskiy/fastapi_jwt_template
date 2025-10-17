import jwt
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidTokenException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


class AuthService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire, "type": token_type, "iat": datetime.utcnow()})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_access_token(data: dict) -> str:
        return AuthService.create_token(
            data, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        return AuthService.create_token(
            data, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

    @staticmethod
    def decode_token(token: str | bytes, expected_type: str = "access") -> dict:
        try:
            if isinstance(token, str):
                token = token.encode("utf-8")
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_type = payload.get("type")
            if token_type != expected_type:
                logger.warning(
                    f"Invalid token type: {token_type}, expected: {expected_type}"
                )
                raise InvalidTokenException()
            return payload
        except jwt.PyJWTError as e:
            logger.warning(f"Token validation error: {e}")
            raise InvalidTokenException()

    @staticmethod
    async def get_current_user(
        token: str, session: AsyncSession, expected_type: str = "access"
    ) -> User:
        payload = AuthService.decode_token(token, expected_type)
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Missing 'sub' in token")
            raise InvalidTokenException()

        user_id = int(user_id)
        user = await UserRepository.get_user_by_id(session, user_id)
        if not user:
            logger.warning(f"User with id {user_id} not found")
            raise InvalidTokenException()
        return user
