import pytest
from sqlalchemy.exc import IntegrityError

from termkeeper.domain import OccurrenceStatus
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Meaning, Occurrence


def test_database_rejects_duplicate_active_meaning_in_same_scope() -> None:
    with get_session() as session:
        session.add(
            Meaning(
                full_name="Order",
                full_name_norm="order",
                scope_id=1,
            ),
        )
        session.add(
            Meaning(
                full_name="order",
                full_name_norm="order",
                scope_id=1,
            ),
        )

        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_database_rejects_inconsistent_occurrence_classification() -> None:
    with get_session() as session:
        session.add(
            Occurrence(
                keyword="ERP",
                keyword_norm="erp",
                status=OccurrenceStatus.RESOLVED,
            ),
        )

        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
