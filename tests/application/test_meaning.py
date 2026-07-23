from uuid import uuid4

import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import MeaningListQuery


def test_validation_and_missing_records_are_explicit() -> None:
    service = TermKeeperService()
    with pytest.raises(ValidationError):
        service.add("  ")
    with pytest.raises(ValidationError):
        service.search_meanings(" ")
    with pytest.raises(NotFoundError):
        service.get_meaning(999)
    with pytest.raises(NotFoundError):
        service.get_meaning_by_public_id(uuid4())
    with pytest.raises(NotFoundError):
        service.get_occurrence(999)


def test_alias_is_idempotent() -> None:
    service = TermKeeperService()
    add_result = service.add("MDM")
    meaning = service.resolve(add_result.occurrence.occurrence_id, "Master Data Management")
    service.add_alias(meaning.meaning_id, "master data management")
    updated = service.add_alias(meaning.meaning_id, "master data management")

    assert len(updated.terms) == 2


def test_edit_lists_and_searches_meanings() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    service.create_scope("SAP S/4HANA")
    captured = service.add("ERP")
    meaning = service.resolve(
        captured.occurrence.occurrence_id,
        "Enterprise Resource Planning",
        scope="SAP",
    )

    edited = service.edit(
        meaning.meaning_id,
        "Enterprise Resource Planning System",
        "suite",
        "SAP S/4HANA",
    )

    assert edited.description == "suite"
    assert edited.scope == "SAP S/4HANA"
    assert "Enterprise Resource Planning System" in edited.terms
    assert service.meanings()[0].meaning_id == meaning.meaning_id
    assert service.search_meanings("SUITE").hits[0].meaning.meaning_id == meaning.meaning_id


def test_meaning_page_filters_and_pages_in_storage() -> None:
    service = TermKeeperService()
    first = service.create_meaning("Alpha")
    service.create_meaning("Beta")
    service.add_tag(first.meaning_id, "Core")
    service.favorite_meaning(first.meaning_id)

    page = service.meaning_page(MeaningListQuery(limit=1))
    filtered = service.meaning_page(
        MeaningListQuery(tag="core", favorite_only=True),
    )

    assert len(page.items) == 1
    assert page.has_more is True
    assert filtered.items == (service.get_meaning(first.meaning_id),)


def test_user_profile_is_recorded_in_audit_columns() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Taro")
    captured = service.add("CRM")
    meaning = service.resolve(
        captured.occurrence.occurrence_id,
        "Customer Relationship Management",
    )

    assert captured.occurrence.created_by_id is not None
    assert meaning.created_by_id == captured.occurrence.created_by_id
    assert meaning.updated_by_id == captured.occurrence.created_by_id


def test_alias_removal_meaning_deletion_and_config_unset() -> None:
    service = TermKeeperService()
    service.set_config("user.email", "taro@example.com")
    captured = service.add("ERP")
    meaning = service.resolve(
        captured.occurrence.occurrence_id,
        "Enterprise Resource Planning",
    )
    service.add_alias(meaning.meaning_id, "enterprise planning")

    updated = service.remove_alias(meaning.meaning_id, "enterprise planning")
    assert "enterprise planning" not in updated.terms
    with pytest.raises(NotFoundError):
        service.remove_alias(meaning.meaning_id, "missing")

    assert service.unset_config("user.email") == {}
    service.delete_meaning(meaning.meaning_id)
    with pytest.raises(NotFoundError):
        service.get_meaning(meaning.meaning_id)


def test_trash_restore_and_purge_protect_occurrence_history() -> None:
    service = TermKeeperService()
    captured = service.add("ERP", source="meeting")
    meaning = service.resolve(
        captured.occurrence.occurrence_id,
        "Enterprise Resource Planning",
    )
    service.add_tag(meaning.meaning_id, "Business")

    service.delete_meaning(meaning.meaning_id)

    assert service.meanings() == []
    assert service.search_meanings("ERP").hits == ()
    recaptured = service.add("ERP")
    assert recaptured.candidates == ()
    trashed = service.trash()[0]
    assert trashed.meaning_id == meaning.meaning_id
    assert trashed.deleted_at is not None
    assert trashed.tags == ("Business",)

    restored = service.restore_meaning(meaning.meaning_id)

    assert restored.deleted_at is None
    assert service.search_meanings("ERP").hits[0].meaning.meaning_id == meaning.meaning_id
    assert service.get_occurrence(recaptured.occurrence.occurrence_id).meaning_id is None
    with pytest.raises(NotFoundError):
        service.restore_meaning(meaning.meaning_id)
    with pytest.raises(NotFoundError):
        service.purge_meaning(meaning.meaning_id)

    service.delete_meaning(meaning.meaning_id)
    with pytest.raises(ValidationError):
        service.purge_meaning(meaning.meaning_id)

    service.unresolve(captured.occurrence.occurrence_id)
    service.purge_meaning(meaning.meaning_id)
    assert service.trash() == []


def test_same_name_is_unique_within_scope_but_allowed_across_scopes() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    service.create_scope("Salesforce")
    service.create_meaning("Order", scope="SAP")

    other = service.create_meaning("Order", scope="Salesforce")

    assert other.scope == "Salesforce"
    with pytest.raises(ValidationError):
        service.create_meaning(" order ", scope=" sap ")
