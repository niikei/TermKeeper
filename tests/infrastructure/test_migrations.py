from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401
from termkeeper.infrastructure.connection import configure_database, get_engine, get_session
from termkeeper.infrastructure.schema import init_db


def test_database_is_upgraded_to_initial_revision() -> None:
    with get_session() as session:
        revision = (
            session.connection()
            .execute(
                text("SELECT version_num FROM alembic_version"),
            )
            .scalar_one()
        )

    assert revision == "0001_initial"


def test_initial_revision_matches_runtime_metadata(tmp_path: Path) -> None:
    configure_database(tmp_path / "fresh.db")
    init_db()

    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, SQLModel.metadata)
        table_names = inspect(connection).get_table_names()

    assert differences == []
    assert "occurrence" in table_names
    assert "inbox" not in table_names
