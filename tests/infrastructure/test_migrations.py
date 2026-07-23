from sqlalchemy import text

from termkeeper.infrastructure.connection import get_session


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
