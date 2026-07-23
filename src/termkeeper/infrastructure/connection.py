"""SQLModel engine and session configuration."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from termkeeper.config import database_path


@dataclass
class _DatabaseState:
    path_override: Path | None = None
    engine: Engine | None = None


_state = _DatabaseState()


def configure_database(path: Path | None) -> None:
    if _state.engine is not None:
        _state.engine.dispose()
    _state.path_override = Path(path) if path is not None else None
    _state.engine = None


def get_engine() -> Engine:
    if _state.engine is None:
        path = (_state.path_override or database_path()).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{path}")

        @event.listens_for(engine, "connect")
        def configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA busy_timeout = 5000")
            cursor.close()

        _state.engine = engine
    return _state.engine


def get_session() -> Session:
    return Session(get_engine())
