import os
from alembic import command
from alembic.config import Config
import anyio


from app.core.logging_config import setup_logger


logger = setup_logger(__name__)
# async def run_migrations():
#     """Применяет все миграции до head."""
#
#     def _run():
#         # Базовая директория
#         base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#         alembic_ini = os.path.join(base_dir, "alembic.ini")
#         alembic_folder = os.path.join(base_dir, "alembic")
#
#         alembic_cfg = Config(alembic_ini)
#         alembic_cfg.set_main_option("script_location", alembic_folder)
#
#         command.upgrade(alembic_cfg, "head")
#
#     # Запуск в отдельном потоке, чтобы не блокировать async event-loop
#     await anyio.to_thread.run_sync(_run)

async def run_migrations():
    """Применяет все миграции до head."""

    def _run():
        base_dir = '/app'
        alembic_ini = os.path.join(base_dir, "alembic.ini")
        alembic_folder = os.path.join(base_dir, "alembic")

        logger.info(f"Running migrations from: {alembic_folder}")

        # Проверяем существование файлов
        if not os.path.exists(alembic_ini):
            logger.info(f"Alembic config not found: {alembic_ini}")
            return

        if not os.path.exists(alembic_folder):
            logger.info(f"Alembic folder not found: {alembic_folder}")
            return

        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option("script_location", alembic_folder)

        try:
            logger.info("Applying database migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations applied successfully")
        except Exception as e:
            logger.error(f"Migration error: {e}")

    await anyio.to_thread.run_sync(_run)