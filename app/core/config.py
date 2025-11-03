from dotenv import load_dotenv
import os

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


load_dotenv()


class Settings:

    if "DB_PORT" not in os.environ:
        logger.warning("CHECK ENV VARIABLES, the application is running with default values!")


    LOCAL_APP: bool = os.getenv("LOCAL_APP", False)

    # Redis for docker
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))

    # DB for docker
    DB_HOST: str = os.getenv("DB_HOST", "db")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PWD: str = os.getenv("DB_PWD", "postgres")

    # Test DB for docker
    TEST_DB_HOST = os.getenv("TEST_DB_HOST", "test_db")
    TEST_DB_PORT = os.getenv("TEST_DB_PORT", "5433")
    TEST_DB_NAME = os.getenv("TEST_DB_NAME", "testdb")
    TEST_DB_USER = os.getenv("TEST_DB_USER", "testuser")
    TEST_DB_PWD = os.getenv("TEST_DB_PWD", "testpass")

    if LOCAL_APP == True:
        logger.info("LOCAL_APP is True, running in local mode")
        # DB for local use
        DB_HOST: str = "localhost"
        DB_PORT: str = "5431"
        # Test DB local use
        TEST_DB_HOST: str = "localhost"
        TEST_DB_PORT: str = "5433"
        # Redis for local use
        REDIS_HOST: str = "localhost"
        REDIS_PORT: int = 6379

    DSN = (f"postgresql+asyncpg://{DB_USER}:{DB_PWD}@{DB_HOST}:"
           f"{DB_PORT}/{DB_NAME}")
    TEST_DSN = (f"postgresql+asyncpg://{TEST_DB_USER}:{TEST_DB_PWD}@{TEST_DB_HOST}:"
                f"{TEST_DB_PORT}/{TEST_DB_NAME}")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    @staticmethod
    def check_variables():
        env_variables = [
            "DB_NAME",
            "DB_USER",
            "DB_PWD",
            "DB_HOST",
            "DB_PORT",
            "TEST_DB_NAME",
            "TEST_DB_USER",
            "TEST_DB_PWD",
            "TEST_DB_HOST",
            "TEST_DB_PORT",
            "PGADMIN_DEFAULT_EMAIL",
            "PGADMIN_DEFAULT_PASSWORD",
            "REDIS_HOST",
            "REDIS_PORT",
            "REDIS_PASSWORD",
            "REDIS_DB",
            "SECRET_KEY",
            "ALGORITHM",
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "REFRESH_TOKEN_EXPIRE_DAYS",
            "LOCAL_APP"
        ]

        missed_var = []
        for var in env_variables:
            if var not in os.environ:
                missed_var.append(var)

        if missed_var:
            logger.warning(f"CHECK ENV VARIABLES, the application is running with default values! "
                           f"Missed variables: {missed_var}")


settings = Settings()
settings.check_variables()
