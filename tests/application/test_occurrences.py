from datetime import UTC, timedelta
from uuid import uuid4

import pytest
from sqlmodel import select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery, OccurrenceUpdate
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Occurrence


def test_occurrences_are_preserved_and_classified_independently() -> None:
    service = TermKeeperService()
    first = service.add("SLA", memo="meeting", source="Teams")
    second = service.add("sla", memo="follow-up", source="Slack")

    meaning = service.resolve(first.occurrence.occurrence_id, "Service Level Agreement")
    service.assign(second.occurrence.occurrence_id, meaning.meaning_id)

    with get_session() as session:
        occurrences = session.exec(
            select(Occurrence).where(Occurrence.meaning_id == meaning.meaning_id),
        ).all()
    assert len(occurrences) == 2
    assert {item.source for item in occurrences} == {"Teams", "Slack"}
    assert all(item.meaning_id == meaning.meaning_id for item in occurrences)


def test_occurrence_history_supports_filters_and_limit() -> None:
    service = TermKeeperService()
    captured = service.add("\uff2d\uff24\uff2d", memo="meeting", source="Teams")
    second = service.add("mdm", memo="follow-up", source="Slack")
    meaning = service.resolve(captured.occurrence.occurrence_id, "Master Data Management")
    service.assign(second.occurrence.occurrence_id, meaning.meaning_id)
    third = service.add("MDM", source="teams")
    service.assign(third.occurrence.occurrence_id, meaning.meaning_id)

    all_items = service.occurrences(
        OccurrenceQuery(meaning_id=meaning.meaning_id),
    ).items

    assert len(all_items) == 3
    assert len(service.occurrences(OccurrenceQuery(keyword="mdm")).items) == 3
    assert len(service.occurrences(OccurrenceQuery(source="TEAMS")).items) == 2
    limited = service.occurrences(OccurrenceQuery(limit=1))
    assert len(limited.items) == 1
    assert limited.has_more is True
    assert all(item.occurred_at.tzinfo is UTC for item in all_items)
    assert (
        len(
            service.occurrences(
                OccurrenceQuery(since=all_items[-1].occurred_at),
            ).items,
        )
        == 3
    )
    since = all_items[-1].occurred_at + timedelta(microseconds=1)
    assert len(service.occurrences(OccurrenceQuery(since=since)).items) == 2


def test_occurrence_history_validates_limit() -> None:
    service = TermKeeperService()

    with pytest.raises(ValidationError):
        service.occurrences(OccurrenceQuery(limit=0))
    with pytest.raises(ValidationError):
        service.occurrences(OccurrenceQuery(limit=501))
    with pytest.raises(ValidationError):
        service.occurrences(OccurrenceQuery(offset=-1))


def test_occurrence_pages_reach_records_beyond_500() -> None:
    with get_session() as session:
        session.add_all(
            [
                Occurrence(keyword=f"TERM-{index}", keyword_norm=f"term-{index}")
                for index in range(505)
            ],
        )
        session.commit()
    service = TermKeeperService()

    first = service.inbox(limit=500)
    tail = service.inbox(offset=500, limit=50)

    assert len(first.items) == 500
    assert first.has_more is True
    assert len(tail.items) == 5
    assert tail.offset == 500
    assert tail.limit == 50
    assert tail.has_more is False
    assert {item.public_id for item in first.items}.isdisjoint(
        item.public_id for item in tail.items
    )


def test_edit_occurrence_updates_context_audit_and_normalized_search() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Editor")
    service.add("ERPP", memo="typo", source="Meeting")
    occurrence = service.occurrences().items[0]

    updated = service.edit_occurrence(
        occurrence.occurrence_id,
        OccurrenceUpdate(keyword=" ERP ", memo=" corrected ", source=" Teams "),
    )

    assert updated.keyword == "ERP"
    assert updated.memo == "corrected"
    assert updated.source == "Teams"
    assert updated.updated_at >= occurrence.updated_at
    assert updated.updated_by_id is not None
    assert (
        service.occurrences(OccurrenceQuery(keyword="erp")).items[0].occurrence_id
        == occurrence.occurrence_id
    )

    cleared = service.edit_occurrence(
        occurrence.occurrence_id,
        OccurrenceUpdate(clear_memo=True, clear_source=True),
    )
    assert cleared.memo is None
    assert cleared.source is None

    public_update = service.edit_occurrence_by_public_id(
        occurrence.public_id,
        OccurrenceUpdate(source="API"),
    )
    assert public_update.source == "API"


def test_edit_occurrence_validation_and_missing_record() -> None:
    service = TermKeeperService()
    service.add("ERP")
    occurrence_id = service.occurrences().items[0].occurrence_id

    invalid_updates = (
        OccurrenceUpdate(),
        OccurrenceUpdate(keyword=" "),
        OccurrenceUpdate(memo=" "),
        OccurrenceUpdate(source=" "),
        OccurrenceUpdate(memo="memo", clear_memo=True),
        OccurrenceUpdate(source="source", clear_source=True),
    )
    for update in invalid_updates:
        with pytest.raises(ValidationError):
            service.edit_occurrence(occurrence_id, update)
    with pytest.raises(NotFoundError):
        service.edit_occurrence(999, OccurrenceUpdate(memo="missing"))
    with pytest.raises(NotFoundError):
        service.edit_occurrence_by_public_id(
            uuid4(),
            OccurrenceUpdate(memo="missing"),
        )
