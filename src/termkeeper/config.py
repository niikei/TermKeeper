"""Runtime configuration without import-time filesystem side effects."""

import os
from pathlib import Path

from platformdirs import user_data_path
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError

DATABASE_URL_ENV = "TERMKEEPER_DATABASE_URL"


def database_path() -> Path:
    """Return the default SQLite path in the OS user data directory."""
    return user_data_path("TermKeeper", appauthor=False) / "termkeeper.db"


def database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    configured = os.environ.get(DATABASE_URL_ENV)
    if configured is not None:
        return configured
    return URL.create(
        "sqlite",
        database=str(database_path().expanduser().resolve()),
    ).render_as_string(hide_password=False)


def database_target() -> str:
    """Return a credential-safe database target for user-facing errors."""
    try:
        return make_url(database_url()).render_as_string(hide_password=True)
    except ArgumentError:
        return f"<invalid {DATABASE_URL_ENV}>"
