import os
from alembic import command
from alembic.config import Config
import anyio


async def run_migrations():
    """Применяет все миграции до head."""

    def _run():
        # Базовая директория
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        alembic_ini = os.path.join(base_dir, "alembic.ini")
        alembic_folder = os.path.join(base_dir, "alembic")

        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option("script_location", alembic_folder)

        command.upgrade(alembic_cfg, "head")

    # Запуск в отдельном потоке, чтобы не блокировать async event-loop
    await anyio.to_thread.run_sync(_run)
