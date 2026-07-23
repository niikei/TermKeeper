import asyncio
from typing import cast

from termkeeper.adapters.mcp_server import TermKeeperMcpTools, create_server
from termkeeper.application import TermKeeperService
from termkeeper.domain import OccurrenceQuery


def test_mcp_server_registers_expected_tools() -> None:
    server = create_server()

    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {
        "add_reference",
        "add_tag",
        "capture_term",
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
        "resolve_inbox",
        "search_meanings",
        "unfavorite_meaning",
        "unrelate_meanings",
    }


def test_mcp_tools_delegate_complete_workflow() -> None:
    service = TermKeeperService()
    tools = TermKeeperMcpTools(service)

    captured = tools.capture_term("ERP", "planning", "Teams")
    captured_inbox = cast("dict[str, object]", captured["inbox"])
    inbox_id = cast("int", captured_inbox["inbox_id"])
    assert tools.list_inbox()[0]["keyword"] == "ERP"
    meaning = tools.resolve_inbox(inbox_id, "Enterprise Resource Planning")
    meaning_id = cast("int", meaning["meaning_id"])

    assert tools.search_meanings("ERP")["hits"]
    assert tools.get_meaning(meaning_id)["full_name"] == "Enterprise Resource Planning"
    assert tools.list_occurrences(OccurrenceQuery(meaning_id=meaning_id))[0]["source"] == "Teams"
    assert tools.get_stats()["total_occurrences"] == 1

    assert tools.add_tag(meaning_id, "SAP")["tags"] == ("SAP",)
    assert tools.list_tags()[0]["name"] == "SAP"
    assert tools.remove_tag(meaning_id, "SAP")["tags"] == ()
    assert tools.favorite_meaning(meaning_id)["is_favorite"] is True
    assert tools.unfavorite_meaning(meaning_id)["is_favorite"] is False

    second = tools.capture_term("MRP")
    second_inbox = cast("dict[str, object]", second["inbox"])
    second_inbox_id = cast("int", second_inbox["inbox_id"])
    related_id = cast(
        "int",
        tools.resolve_inbox(
            second_inbox_id,
            "Material Requirements Planning",
        )["meaning_id"],
    )
    assert tools.relate_meanings(meaning_id, related_id)[0]["meaning_id"] == related_id
    assert tools.list_related(related_id)[0]["meaning_id"] == meaning_id
    assert tools.unrelate_meanings(meaning_id, related_id) == []

    reference = tools.add_reference(
        meaning_id,
        "https://example.com/erp",
        "ERP guide",
    )
    assert reference["title"] == "ERP guide"
    assert tools.list_references(meaning_id)[0]["url"] == "https://example.com/erp"
