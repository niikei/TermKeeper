import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Inbox, Occurrence
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
    with pytest.raises(ValidationError):
        service.search(" ")
    with pytest.raises(NotFoundError):
        service.get_meaning(999)
    with pytest.raises(NotFoundError):
        service.get_inbox(999)


def test_alias_is_idempotent() -> None:
    service = TermKeeperService()
    add_result = service.add("MDM")
    assert add_result.inbox is not None
    inbox = add_result.inbox
    meaning = service.resolve(inbox.inbox_id, "Master Data Management")
    service.add_alias(meaning.meaning_id, "master data management")
    updated = service.add_alias(meaning.meaning_id, "master data management")

    assert len(updated.terms) == 2


def test_edit_lists_and_searches_meanings() -> None:
    service = TermKeeperService()
    captured = service.add("ERP")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Enterprise Resource Planning")

    edited = service.edit(meaning.meaning_id, "Enterprise Resource Planning System", "suite")

    assert edited.description == "suite"
    assert "Enterprise Resource Planning System" in edited.terms
    assert service.meanings()[0].meaning_id == meaning.meaning_id
    assert service.search("SUITE")[0].meaning_id == meaning.meaning_id


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


def test_user_configuration_round_trip_and_validation() -> None:
    service = TermKeeperService()
    with pytest.raises(NotFoundError):
        service.get_config("user.name")

    name = service.set_config("user.name", " Taro Yamada ")
    email = service.set_config("user.email", "taro@example.com")

    assert name["value"] == "Taro Yamada"
    assert service.get_config("user.email") == email
    assert service.list_config() == {
        "user.email": "taro@example.com",
        "user.name": "Taro Yamada",
    }
    with pytest.raises(ValidationError):
        service.get_config("user.name.missing")
    with pytest.raises(ValidationError):
        service.set_config("user.email", "invalid")
    with pytest.raises(ValidationError):
        service.set_config("user.name", " ")


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


def test_user_profile_is_recorded_in_audit_columns() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Taro")
    captured = service.add("CRM")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Customer Relationship Management")

    assert captured.inbox.created_by_id is not None
    assert meaning.created_by_id == captured.inbox.created_by_id
    assert meaning.updated_by_id == captured.inbox.created_by_id


def test_alias_removal_meaning_deletion_and_config_unset() -> None:
    service = TermKeeperService()
    service.set_config("user.email", "taro@example.com")
    captured = service.add("ERP")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Enterprise Resource Planning")
    service.add_alias(meaning.meaning_id, "enterprise planning")

    updated = service.remove_alias(meaning.meaning_id, "enterprise planning")
    assert "enterprise planning" not in updated.terms
    with pytest.raises(NotFoundError):
        service.remove_alias(meaning.meaning_id, "missing")

    assert service.unset_config("user.email") == {}
    service.delete_meaning(meaning.meaning_id)
    with pytest.raises(NotFoundError):
        service.get_meaning(meaning.meaning_id)


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


def test_database_rejects_duplicate_open_inbox() -> None:
    with get_session() as session:
        session.add(Inbox(keyword="CRM", keyword_norm="crm"))
        session.add(Inbox(keyword="crm", keyword_norm="crm"))

        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
