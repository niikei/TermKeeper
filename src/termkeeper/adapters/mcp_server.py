"""Model Context Protocol adapter backed by TermKeeperService."""

from datetime import datetime
from typing import Literal

from mcp.server.fastmcp import FastMCP

from termkeeper.application import TermKeeperService
from termkeeper.domain import OccurrenceQuery, SearchField, SearchQuery

type JsonObject = dict[str, object]


class TermKeeperMcpTools:
    """Typed MCP-facing operations with no protocol or persistence logic."""

    def __init__(self, service: TermKeeperService) -> None:
        self._service = service

    def capture_term(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
    ) -> JsonObject:
        """Capture a term now and preserve where it was encountered."""
        return self._service.add(keyword, memo, source).to_dict()

    def list_inbox(self) -> list[JsonObject]:
        """List unresolved captured terms."""
        return [item.to_dict() for item in self._service.inbox()]

    def resolve_inbox(
        self,
        inbox_id: int,
        full_name: str,
        description: str | None = None,
    ) -> JsonObject:
        """Resolve an inbox item into a searchable meaning."""
        return self._service.resolve(inbox_id, full_name, description).to_dict()

    def search_meanings(
        self,
        text: str,
        field: Literal["all", "term", "name", "description"] = "all",
        tag: str | None = None,
        limit: int = 20,
        *,
        favorite_only: bool = False,
    ) -> JsonObject:
        """Search meanings and return ranked hits or similar suggestions."""
        query = SearchQuery(
            text=text,
            field=SearchField(field),
            limit=limit,
            tag=tag,
            favorite_only=favorite_only,
        )
        return self._service.search(query).to_dict()

    def get_meaning(self, meaning_id: int) -> JsonObject:
        """Get one active meaning by its local ID."""
        return self._service.get_meaning(meaning_id).to_dict()

    def list_occurrences(
        self,
        meaning_id: int | None = None,
        inbox_id: int | None = None,
        keyword: str | None = None,
        source: str | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[JsonObject]:
        """List encounter history with optional filters."""
        query = OccurrenceQuery(
            meaning_id=meaning_id,
            inbox_id=inbox_id,
            keyword=keyword,
            source=source,
            since=since,
            limit=limit,
        )
        return [item.to_dict() for item in self._service.occurrences(query)]

    def get_stats(self, limit: int = 10) -> JsonObject:
        """Get occurrence totals and top term and source rankings."""
        return self._service.stats(limit).to_dict()

    def add_tag(self, meaning_id: int, name: str) -> JsonObject:
        """Add a tag to a meaning."""
        return self._service.add_tag(meaning_id, name).to_dict()

    def remove_tag(self, meaning_id: int, name: str) -> JsonObject:
        """Remove a tag from a meaning."""
        return self._service.remove_tag(meaning_id, name).to_dict()

    def list_tags(self) -> list[JsonObject]:
        """List tags with their active meaning counts."""
        return [item.to_dict() for item in self._service.tags()]

    def favorite_meaning(self, meaning_id: int) -> JsonObject:
        """Mark a meaning as a favorite."""
        return self._service.favorite_meaning(meaning_id).to_dict()

    def unfavorite_meaning(self, meaning_id: int) -> JsonObject:
        """Remove a meaning from favorites."""
        return self._service.unfavorite_meaning(meaning_id).to_dict()

    def relate_meanings(self, meaning_id: int, related_id: int) -> list[JsonObject]:
        """Create a symmetric relationship between two meanings."""
        return [item.to_dict() for item in self._service.relate(meaning_id, related_id)]

    def unrelate_meanings(self, meaning_id: int, related_id: int) -> list[JsonObject]:
        """Remove a relationship between two meanings."""
        return [item.to_dict() for item in self._service.unrelate(meaning_id, related_id)]

    def list_related(self, meaning_id: int) -> list[JsonObject]:
        """List active meanings related to one meaning."""
        return [item.to_dict() for item in self._service.related(meaning_id)]

    def add_reference(
        self,
        meaning_id: int,
        url: str,
        title: str | None = None,
    ) -> JsonObject:
        """Attach an HTTP or HTTPS reference URL to a meaning."""
        return self._service.add_reference(meaning_id, url, title).to_dict()

    def list_references(self, meaning_id: int) -> list[JsonObject]:
        """List reference URLs attached to a meaning."""
        return [item.to_dict() for item in self._service.references(meaning_id)]


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
    ):
        server.add_tool(tool)
    return server


def main() -> None:
    """Run the local MCP server over the standard input/output transport."""
    create_server().run(transport="stdio")  # pragma: no cover - process boundary
