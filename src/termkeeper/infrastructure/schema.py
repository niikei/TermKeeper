"""Alembic-backed schema management."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def init_db() -> None:
    """Upgrade the configured database to the latest schema revision."""
    command.upgrade(migration_config(), "head")


def migration_config() -> Config:
    """Build an Alembic configuration for the packaged migrations."""
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).with_name("migrations")),
    )
    config.attributes["configure_logger"] = False
    return config
