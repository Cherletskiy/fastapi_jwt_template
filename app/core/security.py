import jwt
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidTokenException
from app.core.redis import redis_manager
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
    async def add_to_blacklist(token: str, token_type: str = "access") -> bool:
        """
        Добавляет токен в blacklist
        Returns: True если успешно, False если ошибка
        """
        try:
            if not await redis_manager.is_available():
                logger.warning("Redis not available - skipping blacklist")
                return False

            try:
                payload = AuthService.decode_token(token, expected_type=token_type)
                exp_timestamp = payload.get("exp")

                if exp_timestamp:
                    current_time = datetime.utcnow().timestamp()
                    ttl_seconds = max(0, exp_timestamp - current_time)

                    # Не добавляем уже истекшие токены
                    if ttl_seconds > 0:
                        redis_client = redis_manager.get_client()
                        key = f"blacklist:{token_type}:{token}"
                        await redis_client.setex(key, int(ttl_seconds), "revoked")
                        logger.info(f"Token added to blacklist: {token_type}, TTL: {ttl_seconds}s")
                        return True
                    else:
                        logger.debug(f"Token already expired, skipping blacklist: {token_type}")
                        return True  # Считаем успехом, т.к. токен и так невалиден

            except InvalidTokenException:
                logger.warning(f"Invalid token cannot be added to blacklist: {token}")
                return False

        except Exception as e:
            logger.error(f"Error adding token to blacklist: {e}")
            return False

        return False

    @staticmethod
    async def is_token_revoked(token: str, token_type: str = "access") -> bool:
        """
        Проверяет, находится ли токен в blacklist
        Returns: True если токен отозван, False если валиден
        """
        try:
            if not await redis_manager.is_available():
                logger.warning("Redis not available - blacklist check skipped")
                return False

            redis_client = redis_manager.get_client()
            key = f"blacklist:{token_type}:{token}"
            result = await redis_client.exists(key)

            if result:
                logger.info(f"Token found in blacklist: {token_type}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    @staticmethod
    async def revoke_user_tokens(user_id: int) -> bool:
        """
        Отзывает все токены пользователя (для принудительного логаута)
        В реальном приложении здесь можно хранить jti (JWT ID) для каждого токена
        """
        try:
            if not await redis_manager.is_available():
                return False

            logger.info(f"All tokens revocation requested for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return False

    @staticmethod
    async def get_current_user(
            token: str, session: AsyncSession, expected_type: str = "access"
    ) -> User:
        # проверяем blacklist
        if await AuthService.is_token_revoked(token, expected_type):
            logger.warning(f"Attempt to use revoked {expected_type} token")
            raise InvalidTokenException()

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
