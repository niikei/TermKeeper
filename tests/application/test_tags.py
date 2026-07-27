import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import SearchMode, SearchQuery


def test_tags_are_idempotent_listed_and_filter_meanings_and_search() -> None:
    service = TermKeeperService()
    erp = service.create_meaning("Enterprise Resource Planning", terms=("ERP",))
    crm = service.create_meaning("Customer Relationship Management", terms=("CRM",))

    service.add_tag(erp.meaning_id, "SAP")
    tagged = service.add_tag(erp.meaning_id, "sap")
    service.add_tag(crm.meaning_id, "Sales")

    assert tagged.tags == ("SAP",)
    assert [(tag.name, tag.meaning_count) for tag in service.tags()] == [
        ("Sales", 1),
        ("SAP", 1),
    ]
    assert [item.meaning_id for item in service.meanings("SAP")] == [erp.meaning_id]
    hits = service.search_meanings(SearchQuery("enterprise", tag="sap")).hits
    assert [hit.meaning.meaning_id for hit in hits] == [erp.meaning_id]
    assert service.search_meanings(SearchQuery("customer", tag="SAP")).hits == ()
    assert service.search_meanings(
        SearchQuery("Enterprise*", mode=SearchMode.GLOB, tag="SAP"),
    ).hits

    updated = service.remove_tag(erp.meaning_id, "sAp")
    assert updated.tags == ()
    assert [tag.name for tag in service.tags()] == ["Sales"]


def test_tag_validation_and_missing_assignment() -> None:
    service = TermKeeperService()
    meaning = service.create_meaning("Meaning")
    tagged = service.create_meaning("Tagged Meaning")
    service.add_tag(tagged.meaning_id, "existing")

    with pytest.raises(ValidationError):
        service.add_tag(meaning.meaning_id, " ")
    with pytest.raises(NotFoundError):
        service.remove_tag(meaning.meaning_id, "missing")
    with pytest.raises(NotFoundError):
        service.remove_tag(meaning.meaning_id, "existing")


def test_tag_summaries_exclude_soft_deleted_meanings() -> None:
    service = TermKeeperService()
    active = service.create_meaning("Active")
    deleted = service.create_meaning("Deleted")
    service.add_tag(active.meaning_id, "Shared")
    service.add_tag(deleted.meaning_id, "Shared")

    service.delete_meaning(deleted.meaning_id)

    assert [(tag.name, tag.meaning_count) for tag in service.tags()] == [("Shared", 1)]

    service.restore_meaning(deleted.meaning_id)

    assert [(tag.name, tag.meaning_count) for tag in service.tags()] == [("Shared", 2)]
