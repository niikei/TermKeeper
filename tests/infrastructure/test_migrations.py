from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401
from termkeeper.infrastructure.connection import configure_database, get_engine, get_session
from termkeeper.infrastructure.schema import init_db, migration_config


def test_database_is_upgraded_to_latest_revision() -> None:
    with get_session() as session:
        revision = (
            session.connection()
            .execute(
                text("SELECT version_num FROM alembic_version"),
            )
            .scalar_one()
        )

    assert revision == "0002_description_normalization"


def test_latest_revision_matches_runtime_metadata(tmp_path: Path) -> None:
    configure_database(tmp_path / "fresh.db")
    init_db()

    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, SQLModel.metadata)
        table_names = inspect(connection).get_table_names()

    assert differences == []
    assert "occurrence" in table_names
    assert "inbox" not in table_names


def test_description_normalization_migration_backfills_existing_rows(
    tmp_path: Path,
) -> None:
    configure_database(tmp_path / "legacy.db")
    command.upgrade(migration_config(), "0001_initial")
    with get_engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO meaning ("
                "meaning_id, public_id, full_name, full_name_norm, scope, scope_norm, "
                "description, is_favorite, created_at, updated_at"
                ") VALUES ("
                "1, '00000000000000000000000000000001', 'Legacy', 'legacy', "
                "'General', 'general', 'Ｓｔｒａße', 0, "
                "'2026-07-23 00:00:00', '2026-07-23 00:00:00'"
                ")",
            ),
        )

    command.upgrade(migration_config(), "head")

    with get_engine().connect() as connection:
        description_norm = connection.execute(
            text("SELECT description_norm FROM meaning WHERE meaning_id = 1"),
        ).scalar_one()

    assert description_norm == "strasse"
