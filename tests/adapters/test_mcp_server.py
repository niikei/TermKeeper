import asyncio

from termkeeper.adapters.mcp import (
    OccurrenceFilters,
    SearchFilters,
    TermKeeperMcpTools,
    create_server,
)
from termkeeper.application import TermKeeperService
from termkeeper.domain import OccurrenceUpdate, ReferenceUpdate


def test_mcp_server_registers_expected_tools() -> None:
    server = create_server()

    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {
        "add_reference",
        "add_tag",
        "capture_term",
        "edit_occurrence",
        "edit_reference",
        "favorite_meaning",
        "get_meaning",
        "get_stats",
        "list_inbox",
        "list_occurrences",
        "list_references",
        "list_related",
        "list_tags",
        "relate_meanings",
        "remove_tag",
        "remove_reference",
        "resolve_inbox",
        "search_meanings",
        "unfavorite_meaning",
        "unrelate_meanings",
    }
    schemas = {tool.name: tool.outputSchema for tool in tools}
    capture_schema = schemas["capture_term"]
    meaning_schema = schemas["get_meaning"]
    search_schema = schemas["search_meanings"]
    stats_schema = schemas["get_stats"]
    inbox_schema = schemas["list_inbox"]
    assert capture_schema is not None
    assert meaning_schema is not None
    assert search_schema is not None
    assert stats_schema is not None
    assert inbox_schema is not None
    assert capture_schema["title"] == "ExternalAddResult"
    assert capture_schema["required"] == ["outcome"]
    assert meaning_schema["title"] == "ExternalMeaning"
    assert search_schema["title"] == "ExternalSearchResult"
    assert stats_schema["title"] == "StatsSummary"
    page_schema = inbox_schema["$defs"]["ExternalPage_ExternalInbox_"]
    assert page_schema["properties"]["items"]["items"]["$ref"].endswith(
        "/ExternalInbox",
    )
    definitions = {tool.name: tool.inputSchema for tool in tools}
    assert definitions["get_meaning"]["properties"]["meaning_id"]["format"] == "uuid"
    occurrence_query = definitions["list_occurrences"]["$defs"]["OccurrenceFilters"]
    assert occurrence_query["properties"]["meaning_id"]["anyOf"][0]["format"] == "uuid"
    assert occurrence_query["properties"]["inbox_id"]["anyOf"][0]["format"] == "uuid"
    assert definitions["resolve_inbox"]["properties"]["inbox_id"]["format"] == "uuid"
    assert definitions["edit_occurrence"]["properties"]["occurrence_id"]["format"] == "uuid"


def test_mcp_tools_delegate_complete_workflow() -> None:
    service = TermKeeperService()
    tools = TermKeeperMcpTools(service)

    captured = tools.capture_term("ERP", "planning", "Teams")
    assert captured.inbox is not None
    inbox_id = captured.inbox.public_id
    assert tools.list_inbox().items[0].keyword == "ERP"
    meaning = tools.resolve_inbox(inbox_id, "Enterprise Resource Planning")
    public_id = meaning.public_id

    assert tools.search_meanings(SearchFilters(text="ERP")).hits
    assert tools.get_meaning(public_id).full_name == "Enterprise Resource Planning"
    occurrence = tools.list_occurrences(
        OccurrenceFilters(meaning_id=public_id),
    ).items[0]
    assert occurrence.source == "Teams"
    edited = tools.edit_occurrence(
        occurrence.public_id,
        OccurrenceUpdate(memo="updated by MCP"),
    )
    assert edited.memo == "updated by MCP"
    assert tools.get_stats().total_occurrences == 1
    tools.capture_term("ERP")
    assert (
        tools.list_occurrences(
            OccurrenceFilters(meaning_id=public_id),
        )
        .items[0]
        .inbox_id
        is None
    )

    assert tools.add_tag(public_id, "SAP").tags == ("SAP",)
    assert tools.list_tags().items[0].name == "SAP"
    assert tools.remove_tag(public_id, "SAP").tags == ()
    assert tools.favorite_meaning(public_id).is_favorite is True
    assert tools.unfavorite_meaning(public_id).is_favorite is False

    second = tools.capture_term("MRP")
    assert second.inbox is not None
    related = tools.resolve_inbox(
        second.inbox.public_id,
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
