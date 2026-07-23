from datetime import UTC, timedelta

import pytest
from sqlmodel import select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery, OccurrenceUpdate
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Occurrence


def test_occurrences_are_preserved_and_linked_after_resolve() -> None:
    service = TermKeeperService()
    first = service.add("SLA", memo="meeting", source="Teams")
    service.add("sla", memo="follow-up", source="Slack")
    assert first.inbox is not None

    meaning = service.resolve(first.inbox.inbox_id, "Service Level Agreement")

    with get_session() as session:
        occurrences = session.exec(
            select(Occurrence).where(Occurrence.inbox_id == first.inbox.inbox_id),
        ).all()
    assert len(occurrences) == 2
    assert {item.source for item in occurrences} == {"Teams", "Slack"}
    assert all(item.meaning_id == meaning.meaning_id for item in occurrences)

def test_occurrence_history_supports_filters_and_limit() -> None:
    service = TermKeeperService()
    captured = service.add("\uff2d\uff24\uff2d", memo="meeting", source="Teams")
    service.add("mdm", memo="follow-up", source="Slack")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Master Data Management")
    service.add("MDM", source="teams")

    all_items = service.occurrences(OccurrenceQuery(meaning_id=meaning.meaning_id))

    assert len(all_items) == 3
    assert len(service.occurrences(OccurrenceQuery(inbox_id=captured.inbox.inbox_id))) == 2
    assert len(service.occurrences(OccurrenceQuery(keyword="mdm"))) == 3
    assert len(service.occurrences(OccurrenceQuery(source="TEAMS"))) == 2
    assert len(service.occurrences(OccurrenceQuery(limit=1))) == 1
    aware_since = all_items[-1].occurred_at.replace(tzinfo=UTC)
    assert len(service.occurrences(OccurrenceQuery(since=aware_since))) == 3
    since = all_items[-1].occurred_at + timedelta(microseconds=1)
    assert len(service.occurrences(OccurrenceQuery(since=since))) == 2

def test_occurrence_history_validates_limit() -> None:
    service = TermKeeperService()

    with pytest.raises(ValidationError):
        service.occurrences(OccurrenceQuery(limit=0))
    with pytest.raises(ValidationError):
        service.occurrences(OccurrenceQuery(limit=501))

def test_edit_occurrence_updates_context_audit_and_normalized_search() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Editor")
    service.add("ERPP", memo="typo", source="Meeting")
    occurrence = service.occurrences()[0]

    updated = service.edit_occurrence(
        occurrence.occurrence_id,
        OccurrenceUpdate(keyword=" ERP ", memo=" corrected ", source=" Teams "),
    )

    assert updated.keyword == "ERP"
    assert updated.memo == "corrected"
    assert updated.source == "Teams"
    assert updated.updated_at.replace(tzinfo=None) >= occurrence.updated_at.replace(tzinfo=None)
    assert updated.updated_by_id is not None
    assert service.occurrences(OccurrenceQuery(keyword="erp"))[0].occurrence_id == (
        occurrence.occurrence_id
    )

    cleared = service.edit_occurrence(
        occurrence.occurrence_id,
        OccurrenceUpdate(clear_memo=True, clear_source=True),
    )
    assert cleared.memo is None
    assert cleared.source is None

def test_edit_occurrence_validation_and_missing_record() -> None:
    service = TermKeeperService()
    service.add("ERP")
    occurrence_id = service.occurrences()[0].occurrence_id

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
