"""Alembic-backed schema management."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def init_db() -> None:
    """Upgrade the configured database to the latest schema revision."""
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).with_name("migrations")),
    )
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
