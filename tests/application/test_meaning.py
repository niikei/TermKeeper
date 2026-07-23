from uuid import uuid4

import pytest
from sqlmodel import select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Inbox, Occurrence
from termkeeper.infrastructure.tables import Meaning as MeaningRecord


def test_validation_and_missing_records_are_explicit() -> None:
    service = TermKeeperService()
    with pytest.raises(ValidationError):
        service.add("  ")
    with pytest.raises(ValidationError):
        service.search(" ")
    with pytest.raises(NotFoundError):
        service.get_meaning(999)
    with pytest.raises(NotFoundError):
        service.get_meaning_by_public_id(uuid4())
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
    assert service.search("SUITE").hits[0].meaning.meaning_id == meaning.meaning_id

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

def test_trash_restore_and_purge_preserve_then_remove_related_data() -> None:
    service = TermKeeperService()
    captured = service.add("ERP", source="meeting")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Enterprise Resource Planning")
    service.add_tag(meaning.meaning_id, "Business")

    service.delete_meaning(meaning.meaning_id)

    assert service.meanings() == []
    assert service.search("ERP").hits == ()
    recaptured = service.add("ERP")
    assert recaptured.outcome == "created"
    assert recaptured.inbox is not None
    trashed = service.trash()[0]
    assert trashed.meaning_id == meaning.meaning_id
    assert trashed.deleted_at is not None
    assert trashed.tags == ("Business",)

    restored = service.restore_meaning(meaning.meaning_id)

    assert restored.deleted_at is None
    assert service.search("ERP").hits[0].meaning.meaning_id == meaning.meaning_id
    assert service.get_inbox(recaptured.inbox.inbox_id).resolved_meaning_id == meaning.meaning_id
    with pytest.raises(NotFoundError):
        service.restore_meaning(meaning.meaning_id)
    with pytest.raises(NotFoundError):
        service.purge_meaning(meaning.meaning_id)

    service.delete_meaning(meaning.meaning_id)
    service.purge_meaning(meaning.meaning_id)

    assert service.trash() == []
    with get_session() as session:
        assert session.get(MeaningRecord, meaning.meaning_id) is None
        occurrence = session.exec(
            select(Occurrence).where(Occurrence.inbox_id == captured.inbox.inbox_id),
        ).one()
        inbox = session.get(Inbox, captured.inbox.inbox_id)
    assert occurrence.meaning_id is None
    assert inbox is not None
    assert inbox.resolved_meaning_id is None
