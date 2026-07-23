"""Alembic-backed schema management."""

from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401
from termkeeper.infrastructure.connection import configure_database, get_engine


class SchemaMismatchError(RuntimeError):
    """Raised when an applied revision does not match the packaged schema."""


def init_db() -> None:
    """Upgrade the configured database to the latest schema revision."""
    command.upgrade(migration_config(), "head")
    validate_schema()


def migration_config() -> Config:
    """Build an Alembic configuration for the packaged migrations."""
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).with_name("migrations")),
    )
    config.attributes["configure_logger"] = False
    return config


def schema_revisions() -> tuple[str | None, str]:
    """Return the database and packaged Alembic revisions."""
    config = migration_config()
    expected = ScriptDirectory.from_config(config).get_current_head()
    if expected is None:  # pragma: no cover - the package always has a baseline migration
        message = "TermKeeper has no packaged schema revision."
        raise RuntimeError(message)
    with get_engine().connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    return current, expected


def schema_issues() -> tuple[str, ...]:
    """Return missing tables and columns required by the current build."""
    inspector = inspect(get_engine())
    actual_tables = set(inspector.get_table_names())
    issues: list[str] = []
    for table in SQLModel.metadata.sorted_tables:
        if table.name not in actual_tables:
            issues.append(f"missing table '{table.name}'")
            continue
        actual_columns = {column["name"] for column in inspector.get_columns(table.name)}
        issues.extend(
            f"missing column '{table.name}.{column.name}'"
            for column in table.columns
            if column.name not in actual_columns
        )
    return tuple(issues)


def validate_schema() -> None:
    """Reject a database stamped with a revision whose structure has drifted."""
    issues = schema_issues()
    if not issues:
        return
    details = "; ".join(issues)
    message = (
        f"The database schema does not match this TermKeeper build: {details}. "
        "Run 'tk init --reset' to back up and recreate the database."
    )
    raise SchemaMismatchError(message)


def reset_sqlite_database() -> Path | None:
    """Back up the configured SQLite database and create a fresh schema."""
    engine = get_engine()
    if engine.dialect.name != "sqlite":
        message = "Automatic reset is supported only for SQLite databases."
        raise ValueError(message)
    database = engine.url.database
    if database is None or database == ":memory:":
        message = "An in-memory SQLite database cannot be reset."
        raise ValueError(message)
    url = engine.url.render_as_string(hide_password=False)
    path = Path(database).expanduser().resolve()
    engine.dispose()
    backup = _move_to_backup(path) if path.exists() else None
    configure_database(url)
    init_db()
    return backup


def _move_to_backup(path: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(f"{path.stem}.backup-{timestamp}{path.suffix}")
    path.replace(backup)
    return backup
