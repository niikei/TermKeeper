"""FastMCP server construction and process entry point."""

from mcp.server.fastmcp import FastMCP

from termkeeper.adapters.mcp.tools import TermKeeperMcpTools
from termkeeper.application import TermKeeperService


def create_server(service: TermKeeperService | None = None) -> FastMCP:
    """Create a side-effect-free server, initializing storage only for runtime use."""
    if service is None:
        service = TermKeeperService()
        service.initialize()
    tools = TermKeeperMcpTools(service)
    server = FastMCP(
        "TermKeeper",
        instructions=(
            "Use search_meanings before creating or assigning meanings, and search_scopes "
            "before choosing a scope. Use search_inbox for pending classification work and "
            "search_occurrences for full encounter history. Responses are structured, use "
            "stable UUIDs, and expose has_more plus offset for pagination."
        ),
        json_response=True,
    )
    for tool in (
        tools.capture_term,
        tools.capture_terms,
        tools.create_meaning,
        tools.edit_meaning,
        tools.add_alias,
        tools.remove_alias,
        tools.delete_meaning,
        tools.list_trash,
        tools.restore_meaning,
        tools.list_inbox,
        tools.search_inbox,
        tools.search_meanings,
        tools.search_occurrences,
        tools.search_scopes,
        tools.get_meaning,
        tools.list_meanings,
        tools.list_occurrences,
        tools.edit_occurrence,
        tools.resolve_occurrence,
        tools.assign_occurrence,
        tools.unresolve_occurrence,
        tools.discard_occurrence,
        tools.reopen_occurrence,
        tools.get_stats,
        tools.create_scope,
        tools.list_scopes,
        tools.edit_scope,
        tools.delete_scope,
        tools.add_tag,
        tools.remove_tag,
        tools.list_tags,
        tools.favorite_meaning,
        tools.unfavorite_meaning,
        tools.relate_meanings,
        tools.unrelate_meanings,
        tools.list_related,
        tools.add_reference,
        tools.list_references,
        tools.edit_reference,
        tools.remove_reference,
    ):
        server.add_tool(tool, structured_output=True)
    return server


def main() -> None:
    """Run the local MCP server over the standard input/output transport."""
    create_server().run(transport="stdio")
