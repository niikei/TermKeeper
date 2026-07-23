"""SQLModel engine and session configuration."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, event
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

from termkeeper.config import database_url

SUPPORTED_DATABASE_BACKENDS = frozenset({"postgresql", "sqlite"})


@dataclass
class _DatabaseState:
    url_override: str | None = None
    engine: Engine | None = None


_state = _DatabaseState()


def configure_database(url: str | None) -> None:
    if _state.engine is not None:
        _state.engine.dispose()
    _state.url_override = url
    _state.engine = None


def get_engine() -> Engine:
    if _state.engine is None:
        url = _state.url_override or database_url()
        _validate_backend(url)
        _prepare_sqlite_directory(url)
        engine = create_engine(url)

        if engine.dialect.name == "sqlite":

            @event.listens_for(engine, "connect")
            def configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
                cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA busy_timeout = 5000")
                cursor.close()

        _state.engine = engine
    return _state.engine


def get_session() -> Session:
    return Session(get_engine(), expire_on_commit=False)


def _prepare_sqlite_directory(url: str) -> None:
    parsed = make_url(url)
    database = parsed.database
    if parsed.get_backend_name() != "sqlite" or database is None or database == ":memory:":
        return
    Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _validate_backend(url: str) -> None:
    backend = make_url(url).get_backend_name()
    if backend not in SUPPORTED_DATABASE_BACKENDS:
        supported = ", ".join(sorted(SUPPORTED_DATABASE_BACKENDS))
        message = f"Unsupported database backend '{backend}'. Supported backends: {supported}."
        raise ValueError(message)
