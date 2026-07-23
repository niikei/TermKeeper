"""SQLite connection and runtime database configuration."""

import sqlite3
from pathlib import Path

from termkeeper.config import database_path

_db_path_override: Path | None = None


def configure_database(path: Path | None) -> None:
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def get_connection() -> sqlite3.Connection:
    path = _db_path_override or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection
