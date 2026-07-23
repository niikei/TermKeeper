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
            "Capture unfamiliar terms, resolve them into meanings, and retrieve "
            "searchable organizational terminology."
        ),
        json_response=True,
    )
    for tool in (
        tools.capture_term,
        tools.list_inbox,
        tools.resolve_inbox,
        tools.search_meanings,
        tools.get_meaning,
        tools.list_occurrences,
        tools.edit_occurrence,
        tools.get_stats,
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
