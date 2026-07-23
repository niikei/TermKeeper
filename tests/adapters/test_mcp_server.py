import asyncio
from datetime import UTC

import pytest

from termkeeper.adapters.mcp import (
    CaptureBatchInput,
    CaptureTermInput,
    InboxSearchFilters,
    MeaningCreateInput,
    MeaningEditInput,
    MeaningFilters,
    OccurrenceFilters,
    OccurrenceSearchFilters,
    ScopeSearchFilters,
    SearchFilters,
    TermKeeperMcpTools,
    create_server,
)
from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceUpdate, ReferenceUpdate
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Occurrence


def test_mcp_server_registers_expected_typed_tools() -> None:
    server = create_server()

    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {
        "add_reference",
        "add_alias",
        "add_tag",
        "assign_occurrence",
        "capture_term",
        "capture_terms",
        "create_scope",
        "create_meaning",
        "delete_meaning",
        "delete_scope",
        "discard_occurrence",
        "edit_occurrence",
        "edit_meaning",
        "edit_reference",
        "edit_scope",
        "favorite_meaning",
        "get_meaning",
        "get_stats",
        "list_inbox",
        "list_meanings",
        "list_trash",
        "list_occurrences",
        "list_references",
        "list_related",
        "list_scopes",
        "list_tags",
        "relate_meanings",
        "remove_tag",
        "remove_reference",
        "remove_alias",
        "reopen_occurrence",
        "restore_meaning",
        "resolve_occurrence",
        "search_meanings",
        "search_inbox",
        "search_occurrences",
        "search_scopes",
        "unfavorite_meaning",
        "unrelate_meanings",
        "unresolve_occurrence",
    }
    schemas = {tool.name: tool.outputSchema for tool in tools}
    capture_schema = schemas["capture_term"]
    capture_batch_schema = schemas["capture_terms"]
    meaning_schema = schemas["get_meaning"]
    search_schema = schemas["search_meanings"]
    stats_schema = schemas["get_stats"]
    inbox_schema = schemas["list_inbox"]
    assert capture_schema is not None
    assert capture_batch_schema is not None
    assert meaning_schema is not None
    assert search_schema is not None
    assert stats_schema is not None
    assert inbox_schema is not None
    assert capture_schema["title"] == "ExternalCaptureResult"
    assert capture_schema["required"] == ["occurrence", "candidates"]
    assert capture_batch_schema["title"] == "ExternalCaptureBatchResult"
    assert meaning_schema["title"] == "ExternalMeaning"
    assert search_schema["title"] == "ExternalSearchResult"
    assert stats_schema["title"] == "StatsSummary"
    page_schema = inbox_schema["$defs"]["ExternalPage_ExternalOccurrence_"]
    assert page_schema["properties"]["items"]["items"]["$ref"].endswith(
        "/ExternalOccurrence",
    )
    definitions = {tool.name: tool.inputSchema for tool in tools}
    assert definitions["get_meaning"]["properties"]["meaning_id"]["format"] == "uuid"
    occurrence_query = definitions["list_occurrences"]["$defs"]["OccurrenceFilters"]
    assert occurrence_query["properties"]["meaning_id"]["anyOf"][0]["format"] == "uuid"
    assert definitions["search_inbox"]["$defs"]["InboxSearchFilters"]["required"] == ["text"]
    assert definitions["search_occurrences"]["$defs"]["OccurrenceSearchFilters"]["required"] == [
        "text"
    ]
    assert definitions["search_scopes"]["$defs"]["ScopeSearchFilters"]["required"] == ["text"]
    search_definitions = definitions["search_meanings"]["$defs"]
    assert search_definitions["SearchText"]["minLength"] == 1
    assert search_definitions["SearchText"]["pattern"] == r".*\S.*"
    assert "next page" in search_definitions["Offset"]["description"]
    create_definitions = definitions["create_meaning"]["$defs"]
    assert create_definitions["NonEmptyText"]["minLength"] == 1
    assert create_definitions["NonEmptyText"]["pattern"] == r".*\S.*"
    assert create_definitions["MeaningCreateInput"]["properties"]["full_name"] == {
        "$ref": "#/$defs/NonEmptyText"
    }
    assert definitions["add_alias"]["properties"]["alias"] == {"$ref": "#/$defs/NonEmptyText"}
    assert definitions["resolve_occurrence"]["properties"]["occurrence_id"]["format"] == "uuid"
    assert definitions["edit_occurrence"]["properties"]["occurrence_id"]["format"] == "uuid"
    capture_batch_definitions = definitions["capture_terms"]["$defs"]
    assert capture_batch_definitions["CaptureItems"]["minItems"] == 1
    assert capture_batch_definitions["CaptureItems"]["maxItems"] == 100
    assert capture_batch_definitions["NonEmptyText"]["pattern"] == r".*\S.*"


def test_mcp_meaning_lifecycle_is_safe_and_reversible() -> None:
    tools = TermKeeperMcpTools(TermKeeperService())
    scope = tools.create_scope("SAP")
    created = tools.create_meaning(
        MeaningCreateInput(
            "Enterprise Resource Planning",
            scope.public_id,
            aliases=("ERP",),
        ),
    )

    assert tools.add_alias(created.public_id, "ERP System").terms == (
        "Enterprise Resource Planning",
        "ERP",
        "ERP System",
    )
    assert tools.remove_alias(created.public_id, "ERP System").public_id == created.public_id
    edited = tools.edit_meaning(
        created.public_id,
        MeaningEditInput("Enterprise Resource Planning Suite", scope.public_id),
    )
    assert edited.full_name == "Enterprise Resource Planning Suite"

    assert tools.delete_meaning(created.public_id) == {"meaning_id": created.public_id}
    assert tools.list_trash().items[0].public_id == created.public_id
    assert tools.restore_meaning(created.public_id).public_id == created.public_id


def test_mcp_batch_capture_is_typed_atomic_and_ordered() -> None:
    service = TermKeeperService()
    tools = TermKeeperMcpTools(service)

    result = tools.capture_terms(
        CaptureBatchInput(
            (
                CaptureTermInput("ERP", source="Teams"),
                CaptureTermInput("Business Unit", memo="SAP context"),
            ),
        ),
    )

    assert [item.occurrence.keyword for item in result.items] == [
        "ERP",
        "Business Unit",
    ]
    assert result.items[0].occurrence.source == "Teams"
    assert result.items[1].occurrence.memo == "SAP context"

    with pytest.raises(ValidationError, match="duplicates position"):
        tools.capture_terms(
            CaptureBatchInput(
                (CaptureTermInput("CRM"), CaptureTermInput("ＣＲＭ")),
            ),
        )
    assert len(service.history().items) == 2


def test_mcp_tools_delegate_complete_workflow() -> None:
    service = TermKeeperService()
    tools = TermKeeperMcpTools(service)
    sap_scope = tools.create_scope("SAP")
    assert tools.list_meanings(MeaningFilters()).items == ()

    captured = tools.capture_term("ERP", "planning", "Teams")
    occurrence_id = captured.occurrence.public_id
    assert captured.occurrence.status == "Pending"
    assert captured.occurrence.occurred_at.tzinfo is UTC
    assert captured.occurrence.updated_at.tzinfo is UTC
    assert tools.list_inbox().items[0].keyword == "ERP"
    assert tools.search_inbox(InboxSearchFilters(text="planning")).items[0].keyword == "ERP"
    assert tools.search_occurrences(OccurrenceSearchFilters(text="Teams")).items[0].keyword == "ERP"
    meaning = tools.resolve_occurrence(
        occurrence_id,
        "Enterprise Resource Planning",
        sap_scope.public_id,
    )
    public_id = meaning.public_id

    assert meaning.scope == "SAP"
    assert tools.search_meanings(SearchFilters(text="ERP")).hits
    assert tools.get_meaning(public_id).full_name == "Enterprise Resource Planning"
    occurrence = tools.list_occurrences(
        OccurrenceFilters(meaning_id=public_id),
    ).items[0]
    assert occurrence.source == "Teams"
    assert occurrence.occurred_at.tzinfo is UTC
    edited = tools.edit_occurrence(
        occurrence.public_id,
        OccurrenceUpdate(memo="updated by MCP"),
    )
    assert edited.memo == "updated by MCP"
    assert tools.get_stats().total_occurrences == 1

    pending = tools.capture_term("ERP")
    assert [item.public_id for item in pending.candidates] == [public_id]
    assigned = tools.assign_occurrence(pending.occurrence.public_id, public_id)
    assert assigned.meaning_id == public_id
    assert tools.unresolve_occurrence(assigned.public_id).status == "Pending"
    assert tools.discard_occurrence(assigned.public_id).status == "Discarded"
    assert tools.reopen_occurrence(assigned.public_id).status == "Pending"

    assert tools.add_tag(public_id, "SAP").tags == ("SAP",)
    assert tools.list_tags().items[0].name == "SAP"
    assert tools.remove_tag(public_id, "SAP").tags == ()
    assert tools.favorite_meaning(public_id).is_favorite is True
    assert tools.unfavorite_meaning(public_id).is_favorite is False

    second = tools.capture_term("MRP")
    related = tools.resolve_occurrence(
        second.occurrence.public_id,
        "Material Requirements Planning",
    )
    assert tools.relate_meanings(public_id, related.public_id)[0].public_id == related.public_id
    assert tools.list_related(related.public_id).items[0].public_id == public_id
    assert tools.unrelate_meanings(public_id, related.public_id) == []

    reference = tools.add_reference(
        public_id,
        "https://example.com/erp",
        "ERP guide",
    )
    assert reference.title == "ERP guide"
    assert tools.list_references(public_id).items[0].url == "https://example.com/erp"
    edited_reference = tools.edit_reference(
        reference.public_id,
        ReferenceUpdate(title="Updated guide"),
    )
    assert edited_reference.title == "Updated guide"
    assert tools.remove_reference(reference.public_id).public_id == reference.public_id

    service.delete_meaning(service.get_meaning_by_public_id(public_id).meaning_id)
    assert (
        tools.list_occurrences(
            OccurrenceFilters(meaning_id=public_id),
        )
        .items[0]
        .meaning_id
        == public_id
    )
    spare_scope = tools.create_scope("Temporary")
    assert any(item.public_id == spare_scope.public_id for item in tools.list_scopes().items)
    assert tools.search_scopes(ScopeSearchFilters(text="tempor")).items[0].public_id == (
        spare_scope.public_id
    )
    renamed_scope = tools.edit_scope(spare_scope.public_id, "Temporary 2")
    assert renamed_scope.name == "Temporary 2"
    assert tools.delete_scope(spare_scope.public_id) == {"scope_id": spare_scope.public_id}


def test_mcp_occurrence_pages_reach_beyond_500() -> None:
    with get_session() as session:
        session.add_all(
            [
                Occurrence(keyword=f"TERM-{index}", keyword_norm=f"term-{index}")
                for index in range(505)
            ],
        )
        session.commit()
    tools = TermKeeperMcpTools(TermKeeperService())

    first = tools.list_inbox(limit=100)
    tail = tools.list_occurrences(OccurrenceFilters(offset=500, limit=10))

    assert len(first.items) == 100
    assert first.has_more is True
    assert len(tail.items) == 5
    assert tail.offset == 500
    assert tail.has_more is False
