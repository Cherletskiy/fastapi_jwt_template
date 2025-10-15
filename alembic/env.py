from sqlalchemy import engine_from_config, pool
from alembic import context

from app.models.user import Base
from app.core.config import settings

# Инициализация Alembic config
config = context.config

# Заменяем asyncpg на sync драйвер для миграций
sync_dsn = settings.DSN.replace("postgresql+asyncpg", "postgresql")
config.set_main_option("sqlalchemy.url", sync_dsn)

# # для локального тестирования
# sync_dsn = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@localhost:5431/{settings.DB_NAME}"
# config.set_main_option("sqlalchemy.url", sync_dsn)

# Метаданные для автогенерации миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()