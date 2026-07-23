from datetime import UTC, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery, OccurrenceUpdate, SearchField, SearchQuery
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
        service.search(SearchQuery("term", limit=101))
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
    hits = service.search(SearchQuery("enterprise", tag="sap")).hits
    assert [hit.meaning.meaning_id for hit in hits] == [erp.meaning_id]
    assert service.search(SearchQuery("customer", tag="SAP")).hits == ()

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


def test_merge_meanings_moves_terms_occurrences_and_inboxes() -> None:
    service = TermKeeperService()
    captured_source = service.add("SRC", source="Teams")
    service.add("src", source="Slack")
    captured_target = service.add("TGT")
    assert captured_source.inbox is not None
    assert captured_target.inbox is not None
    source = service.resolve(captured_source.inbox.inbox_id, "Source Meaning")
    target = service.resolve(captured_target.inbox.inbox_id, "Target Meaning")
    service.add_alias(source.meaning_id, "shared")
    service.add_alias(source.meaning_id, "source-only")
    service.add_alias(target.meaning_id, "shared")
    service.add_tag(source.meaning_id, "source-tag")
    service.add_tag(source.meaning_id, "shared-tag")
    service.add_tag(target.meaning_id, "shared-tag")

    preview = service.merge_meanings(source.meaning_id, target.meaning_id, dry_run=True)

    assert preview.terms_moved == 3
    assert preview.tags_moved == 1
    assert preview.occurrences_moved == 2
    assert preview.inboxes_moved == 1
    assert preview.applied is False
    assert service.get_meaning(source.meaning_id).full_name == "Source Meaning"

    result = service.merge_meanings(source.meaning_id, target.meaning_id)

    assert result.applied is True
    with pytest.raises(NotFoundError):
        service.get_meaning(source.meaning_id)
    merged = service.get_meaning(target.meaning_id)
    assert {"SRC", "Source Meaning", "shared", "source-only"} <= set(merged.terms)
    assert set(merged.tags) == {"source-tag", "shared-tag"}
    assert service.occurrences(OccurrenceQuery(meaning_id=source.meaning_id)) == []
    assert len(service.occurrences(OccurrenceQuery(meaning_id=target.meaning_id))) == 3
    source_inbox = service.get_inbox(captured_source.inbox.inbox_id)
    assert source_inbox.resolved_meaning_id == target.meaning_id


def test_merge_validation_and_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TermKeeperService()
    source = service.create_meaning("Source", terms=("source-alias",))
    target = service.create_meaning("Target")

    with pytest.raises(ValidationError):
        service.merge_meanings(source.meaning_id, source.meaning_id)

    def fail_move(*_args: object, **_kwargs: object) -> tuple[int, int]:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "termkeeper.application.use_cases.merge.inbox_repository.move_meaning_references",
        fail_move,
    )
    with pytest.raises(RuntimeError):
        service.merge_meanings(source.meaning_id, target.meaning_id)

    assert "source-alias" in service.get_meaning(source.meaning_id).terms
    assert "source-alias" not in service.get_meaning(target.meaning_id).terms


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
