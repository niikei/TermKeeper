import pytest

from termkeeper.service import NotFoundError, TermKeeperService, ValidationError


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


def test_resolve_creates_searchable_meaning_and_closes_inbox() -> None:
    service = TermKeeperService()
    add_result = service.add("BTP")
    assert add_result.inbox is not None
    item = add_result.inbox
    meaning = service.resolve(item.inbox_id, "Business Technology Platform", "SAP platform")

    assert set(meaning.terms) == {"BTP", "Business Technology Platform"}
    assert service.get_inbox(item.inbox_id).status == "Closed"
    assert service.search("sap")[0].meaning_id == meaning.meaning_id
    assert service.add("btp").outcome == "registered"


def test_validation_and_missing_records_are_explicit() -> None:
    service = TermKeeperService()
    with pytest.raises(ValidationError):
        service.add("  ")
    with pytest.raises(NotFoundError):
        service.get_meaning(999)


def test_alias_is_idempotent() -> None:
    service = TermKeeperService()
    add_result = service.add("MDM")
    assert add_result.inbox is not None
    inbox = add_result.inbox
    meaning = service.resolve(inbox.inbox_id, "Master Data Management")
    service.add_alias(meaning.meaning_id, "master data management")
    updated = service.add_alias(meaning.meaning_id, "master data management")

    assert len(updated.terms) == 2
