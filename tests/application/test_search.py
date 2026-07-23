import pytest

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import SearchField, SearchQuery


def test_search_ranks_matches_and_reports_reason() -> None:
    service = TermKeeperService()
    exact = service.create_meaning("Enterprise Resource Planning", terms=("ERP",))
    prefix = service.create_meaning("ERP Cloud")
    description = service.create_meaning("Finance Suite", "Supports ERP workflows")

    hits = service.search("ERP").hits

    assert [hit.meaning.meaning_id for hit in hits] == [
        exact.meaning_id,
        prefix.meaning_id,
        description.meaning_id,
    ]
    assert hits[0].score == 100
    assert hits[0].matched_field == SearchField.TERM
    assert hits[0].matched_text == "ERP"


def test_search_supports_multiple_words_fields_modes_and_limit() -> None:
    service = TermKeeperService()
    erp = service.create_meaning(
        "Enterprise Resource Planning",
        "Core business planning",
        ("ERP",),
    )
    service.create_meaning("Enterprise Content Management", "Document platform", ("ECM",))

    assert service.search("enterprise planning").hits[0].meaning.meaning_id == erp.meaning_id
    assert service.search("enterprise missing").hits == ()
    assert len(service.search(SearchQuery("planning document", match_all=False)).hits) == 2
    assert (
        service.search(SearchQuery("business", field=SearchField.DESCRIPTION))
        .hits[0]
        .meaning.meaning_id
        == erp.meaning_id
    )
    assert service.search(SearchQuery("enterprise", field=SearchField.DESCRIPTION)).hits == ()
    assert len(service.search(SearchQuery("enterprise", limit=1)).hits) == 1


def test_search_treats_sql_wildcards_as_text_and_validates_limit() -> None:
    service = TermKeeperService()
    percent = service.create_meaning("100% Completion")
    service.create_meaning("Unrelated")

    hits = service.search("%").hits

    assert [hit.meaning.meaning_id for hit in hits] == [percent.meaning_id]
    with pytest.raises(ValidationError):
        service.search(SearchQuery("term", limit=0))
    with pytest.raises(ValidationError):
        service.search(SearchQuery("term", limit=501))
    with pytest.raises(ValidationError):
        service.search(SearchQuery("term", suggestion_limit=11))


def test_search_suggests_similar_active_meanings_only_when_no_hits() -> None:
    service = TermKeeperService()
    erp = service.create_meaning("Enterprise Resource Planning", terms=("ERP",))
    service.add_tag(erp.meaning_id, "SAP")
    archived = service.create_meaning("ERPP Archive", terms=("ERPP",))
    service.delete_meaning(archived.meaning_id)

    result = service.search(SearchQuery("ERPP", tag="SAP"))

    assert result.hits == ()
    assert len(result.suggestions) == 1
    suggestion = result.suggestions[0]
    assert suggestion.meaning.meaning_id == erp.meaning_id
    assert suggestion.matched_field == SearchField.TERM
    assert suggestion.matched_text == "ERP"
    assert suggestion.similarity == 86

    exact = service.search("ERP")
    assert exact.hits
    assert exact.suggestions == ()
    assert service.search(SearchQuery("ERPP", suggestion_limit=0)).suggestions == ()


def test_description_search_has_no_suggestion_without_descriptions() -> None:
    service = TermKeeperService()
    service.create_meaning("Enterprise Resource Planning")

    result = service.search(SearchQuery("planning", field=SearchField.DESCRIPTION))

    assert result.hits == ()
    assert result.suggestions == ()


def test_search_normalizes_unicode_names_and_descriptions() -> None:
    service = TermKeeperService()
    german = service.create_meaning("Straße")
    full_width = service.create_meaning(
        "Finance",
        "ＳＡＰ　Ｐｌａｎｎｉｎｇ",
    )

    name_result = service.search(SearchQuery("STRASSE", field=SearchField.NAME))
    description_result = service.search(
        SearchQuery("sap planning", field=SearchField.DESCRIPTION),
    )

    assert name_result.hits[0].meaning.meaning_id == german.meaning_id
    assert name_result.hits[0].matched_text == "Straße"
    assert description_result.hits[0].meaning.meaning_id == full_width.meaning_id
    assert description_result.hits[0].matched_text == "ＳＡＰ　Ｐｌａｎｎｉｎｇ"

    service.edit(
        full_width.meaning_id,
        full_width.full_name,
        "Ｃｕｓｔｏｍｅｒ　Ｄａｔａ",
    )
    assert (
        service.search(SearchQuery("customer data", field=SearchField.DESCRIPTION))
        .hits[0]
        .meaning.meaning_id
        == full_width.meaning_id
    )


def test_search_and_list_filter_ambiguous_terms_by_scope() -> None:
    service = TermKeeperService()
    sap = service.create_meaning(
        "Enterprise Resource Planning",
        terms=("ERP",),
        scope="SAP",
    )
    service.create_meaning(
        "Effective Radiated Power",
        terms=("ERP",),
        scope="Radio",
    )

    result = service.search(SearchQuery("ERP", scope="sap"))

    assert [hit.meaning.meaning_id for hit in result.hits] == [sap.meaning_id]
    assert [item.meaning_id for item in service.meanings(scope="SAP")] == [
        sap.meaning_id,
    ]
