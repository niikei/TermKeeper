from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401
from termkeeper.infrastructure.connection import configure_database, get_engine, get_session
from termkeeper.infrastructure.schema import (
    EXPECTED_SCHEMA_REVISION,
    init_db,
    migration_config,
)


def test_database_is_upgraded_to_latest_revision() -> None:
    with get_session() as session:
        revision = (
            session.connection()
            .execute(
                text("SELECT version_num FROM alembic_version"),
            )
            .scalar_one()
        )

    assert revision == EXPECTED_SCHEMA_REVISION


def test_expected_revision_matches_packaged_migration_head() -> None:
    assert (
        ScriptDirectory.from_config(migration_config()).get_current_head()
        == EXPECTED_SCHEMA_REVISION
    )


def test_latest_revision_matches_runtime_metadata(tmp_path: Path) -> None:
    configure_database(f"sqlite:///{tmp_path / 'fresh.db'}")
    init_db()

    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, SQLModel.metadata)
        table_names = inspect(connection).get_table_names()

    assert differences == []
    assert "occurrence" in table_names
    assert "inbox" not in table_names
