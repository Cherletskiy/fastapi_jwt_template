import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


class RedisManager:
    def __init__(self):
        self.redis_client = None

    async def init_redis(self):
        """Инициализация Redis подключения"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Проверяем подключение
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # В тестовом режиме можем продолжить без Redis
            logger.warning("Continuing without Redis - blacklist will not work")

    async def close_redis(self):
        """Закрытие Redis подключения"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    def get_client(self) -> redis.Redis:
        """Получение Redis клиента"""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client

    async def is_available(self) -> bool:
        """Проверка доступности Redis"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception:
            return False


# Глобальный экземпляр
redis_manager = RedisManager()