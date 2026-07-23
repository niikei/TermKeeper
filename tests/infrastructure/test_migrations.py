from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from termkeeper.infrastructure.connection import configure_database, get_engine, get_session
from termkeeper.infrastructure.schema import init_db


def test_database_is_upgraded_to_latest_revision() -> None:
    with get_session() as session:
        revision = (
            session.connection()
            .execute(
                text("SELECT version_num FROM alembic_version"),
            )
            .scalar_one()
        )

    assert revision == "0002_occurrence_classification"


def test_legacy_automatic_assignments_are_returned_to_pending(tmp_path: Path) -> None:
    configure_database(tmp_path / "legacy.db")
    config = _migration_config()
    command.upgrade(config, "0001_initial")
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO meaning (
                    meaning_id, public_id, full_name, is_favorite, created_at, updated_at
                ) VALUES (
                    1, '00000000000000000000000000000001',
                    'Enterprise Resource Planning', 0,
                    '2026-01-01 00:00:00', '2026-01-01 00:00:00'
                )
                """,
            ),
        )
        connection.execute(
            text(
                """
                INSERT INTO inbox (
                    inbox_id, public_id, keyword, keyword_norm, status,
                    resolved_meaning_id, created_at, updated_at, closed_at
                ) VALUES (
                    1, '00000000000000000000000000000002',
                    'ERP', 'erp', 'CLOSED', 1,
                    '2026-01-01 00:00:00', '2026-01-01 00:00:00',
                    '2026-01-01 00:00:00'
                )
                """,
            ),
        )
        connection.execute(
            text(
                """
                INSERT INTO occurrence (
                    occurrence_id, public_id, keyword, keyword_norm, inbox_id, meaning_id,
                    occurred_at, updated_at
                ) VALUES
                    (
                        1, '00000000000000000000000000000003',
                        'ERP', 'erp', 1, 1,
                        '2026-01-01 00:00:00', '2026-01-01 00:00:00'
                    ),
                    (
                        2, '00000000000000000000000000000004',
                        'ERP', 'erp', NULL, 1,
                        '2026-01-02 00:00:00', '2026-01-02 00:00:00'
                    )
                """,
            ),
        )

    init_db()

    with get_engine().connect() as connection:
        rows = connection.execute(
            text(
                "SELECT occurrence_id, status, meaning_id FROM occurrence ORDER BY occurrence_id",
            ),
        ).all()
        scope = connection.execute(text("SELECT scope FROM meaning")).scalar_one()
        tables = inspect(connection).get_table_names()

    assert rows == [(1, "RESOLVED", 1), (2, "PENDING", None)]
    assert scope == "General"
    assert "inbox" not in tables


def _migration_config() -> Config:
    config = Config()
    config.set_main_option(
        "script_location",
        str(Path(__file__).parents[2] / "src" / "termkeeper" / "infrastructure" / "migrations"),
    )
    config.attributes["configure_logger"] = False
    return config
