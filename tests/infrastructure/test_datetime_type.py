from datetime import UTC, datetime, timedelta, timezone

import pytest

from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Occurrence
from termkeeper.infrastructure.types import UTCDateTime

DATETIME_COLUMNS = {
    ("meaning", "created_at"),
    ("meaning", "deleted_at"),
    ("meaning", "updated_at"),
    ("meaningreference", "created_at"),
    ("meaningreference", "updated_at"),
    ("meaningrelation", "created_at"),
    ("meaningtag", "created_at"),
    ("occurrence", "discarded_at"),
    ("occurrence", "occurred_at"),
    ("occurrence", "resolved_at"),
    ("occurrence", "updated_at"),
    ("tag", "created_at"),
    ("term", "created_at"),
    ("term", "updated_at"),
    ("userprofile", "created_at"),
    ("userprofile", "updated_at"),
}


def test_all_datetime_columns_use_the_utc_type() -> None:
    actual = {
        (column.table.name, column.name)
        for table in Occurrence.metadata.sorted_tables
        for column in table.columns
        if isinstance(column.type, UTCDateTime)
    }

    assert actual == DATETIME_COLUMNS


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2026, 7, 23, 12, 30, tzinfo=timezone(timedelta(hours=9))),
            datetime(2026, 7, 23, 3, 30, tzinfo=UTC),
        ),
        (
            datetime(2026, 7, 23, 3, 30),
            datetime(2026, 7, 23, 3, 30, tzinfo=UTC),
        ),
    ],
)
def test_datetime_is_reloaded_as_utc(value: datetime, expected: datetime) -> None:
    with get_session() as session:
        occurrence = Occurrence(
            keyword="UTC",
            keyword_norm="utc",
            occurred_at=value,
        )
        session.add(occurrence)
        session.commit()
        occurrence_id = occurrence.occurrence_id

    with get_session() as session:
        reloaded = session.get(Occurrence, occurrence_id)

    assert reloaded is not None
    assert reloaded.occurred_at == expected
    assert reloaded.occurred_at.tzinfo is UTC
    assert reloaded.updated_at.tzinfo is UTC
