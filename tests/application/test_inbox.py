from uuid import uuid4

import pytest
from sqlmodel import func, select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Meaning as MeaningRecord


def test_capture_duplicate_increments_occurrence_count() -> None:
    service = TermKeeperService()
    # Full-width input verifies that NFKC normalization prevents duplicates.
    first = service.add("\uff2d\uff24\uff2d", memo="meeting")
    second = service.add("mdm", source="chat")

    assert first.outcome == "created"
    assert second.outcome == "seen_again"
    assert second.inbox is not None
    assert second.inbox.occurrence_count == 2
    assert second.inbox.memo == "meeting"
    assert second.inbox.source == "chat"


def test_edit_open_inbox_validates_state_and_duplicates() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Editor")
    first = service.add("ERPP")
    second = service.add("CRM")
    assert first.inbox is not None
    assert second.inbox is not None

    edited = service.edit_inbox(first.inbox.inbox_id, " ERP ")

    assert edited.keyword == "ERP"
    assert edited.updated_by_id is not None
    assert service.occurrences(OccurrenceQuery(inbox_id=first.inbox.inbox_id))[0].keyword == "ERPP"
    with pytest.raises(ValidationError):
        service.edit_inbox(second.inbox.inbox_id, " ")
    with pytest.raises(ValidationError):
        service.edit_inbox(second.inbox.inbox_id, "ERP")
    meaning = service.resolve(first.inbox.inbox_id, "Enterprise Resource Planning")
    assert "ERP" in meaning.terms
    with pytest.raises(ValidationError):
        service.edit_inbox(first.inbox.inbox_id, "ERP updated")


def test_resolve_creates_searchable_meaning_and_closes_inbox() -> None:
    service = TermKeeperService()
    add_result = service.add("BTP")
    assert add_result.inbox is not None
    item = add_result.inbox
    meaning = service.resolve(item.inbox_id, "Business Technology Platform", "SAP platform")

    assert set(meaning.terms) == {"BTP", "Business Technology Platform"}
    assert service.get_inbox(item.inbox_id).status == "Closed"
    assert service.search("sap").hits[0].meaning.meaning_id == meaning.meaning_id
    assert service.add("btp").outcome == "registered"


def test_get_inbox_by_public_id_reports_missing_item() -> None:
    service = TermKeeperService()

    with pytest.raises(NotFoundError):
        service.get_inbox_by_public_id(uuid4())


def test_discard_updates_history_and_prevents_repeated_actions() -> None:
    service = TermKeeperService()
    captured = service.add("obsolete")
    assert captured.inbox is not None

    service.discard(captured.inbox.inbox_id)

    assert service.inbox() == []
    assert service.history()[0].status == "Discarded"
    with pytest.raises(NotFoundError):
        service.discard(captured.inbox.inbox_id)
    with pytest.raises(ValidationError):
        service.resolve(captured.inbox.inbox_id, "Obsolete")


def test_resolve_and_alias_validation() -> None:
    service = TermKeeperService()
    captured = service.add("blank")
    assert captured.inbox is not None

    with pytest.raises(ValidationError):
        service.resolve(captured.inbox.inbox_id, " ")
    meaning = service.resolve(captured.inbox.inbox_id, "Blank")
    with pytest.raises(ValidationError):
        service.add_alias(meaning.meaning_id, " ")
    with pytest.raises(ValidationError):
        service.edit(meaning.meaning_id, " ", None)


def test_resolve_rolls_back_all_changes_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TermKeeperService()
    captured = service.add("TX")
    assert captured.inbox is not None

    def fail_add_term(*_args: object, **_kwargs: object) -> bool:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "termkeeper.application.use_cases.inbox.meaning_repository.add_term",
        fail_add_term,
    )
    with pytest.raises(RuntimeError):
        service.resolve(captured.inbox.inbox_id, "Transaction")

    assert service.get_inbox(captured.inbox.inbox_id).status == "New"
    with get_session() as session:
        meaning_count = session.exec(select(func.count()).select_from(MeaningRecord)).one()
    assert meaning_count == 0
