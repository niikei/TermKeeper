"""Model Context Protocol adapter backed by TermKeeperService."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    AddResult,
    InboxItem,
    Meaning,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceUpdate,
    ReferenceLink,
    SearchField,
    SearchQuery,
    SearchResult,
    StatsSummary,
    TagSummary,
)


@dataclass(frozen=True)
class OccurrenceFilters:
    meaning_id: UUID | None = None
    inbox_id: UUID | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    limit: int = 50


class TermKeeperMcpTools:
    """Typed MCP-facing operations with no protocol or persistence logic."""

    def __init__(self, service: TermKeeperService) -> None:
        self._service = service

    def capture_term(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
    ) -> AddResult:
        """Capture a term now and preserve where it was encountered."""
        return self._service.add(keyword, memo, source)

    def list_inbox(self) -> list[InboxItem]:
        """List unresolved captured terms."""
        return self._service.inbox()

    def resolve_inbox(
        self,
        inbox_id: UUID,
        full_name: str,
        description: str | None = None,
    ) -> Meaning:
        """Resolve an inbox item into a searchable meaning."""
        return self._service.resolve(
            self._local_inbox_id(inbox_id),
            full_name,
            description,
        )

    def search_meanings(
        self,
        text: str,
        field: Literal["all", "term", "name", "description"] = "all",
        tag: str | None = None,
        limit: int = 20,
        *,
        favorite_only: bool = False,
    ) -> SearchResult:
        """Search meanings and return ranked hits or similar suggestions."""
        query = SearchQuery(
            text=text,
            field=SearchField(field),
            limit=limit,
            tag=tag,
            favorite_only=favorite_only,
        )
        return self._service.search(query)

    def get_meaning(self, meaning_id: UUID) -> Meaning:
        """Get one active meaning by its stable UUID."""
        return self._service.get_meaning_by_public_id(meaning_id)

    def list_occurrences(
        self,
        query: OccurrenceFilters | None = None,
    ) -> list[OccurrenceItem]:
        """List encounter history with optional filters."""
        query = query or OccurrenceFilters()
        meaning_id = (
            self._local_meaning_id(query.meaning_id) if query.meaning_id is not None else None
        )
        inbox_id = self._local_inbox_id(query.inbox_id) if query.inbox_id is not None else None
        return self._service.occurrences(
            OccurrenceQuery(
                meaning_id=meaning_id,
                inbox_id=inbox_id,
                keyword=query.keyword,
                source=query.source,
                since=query.since,
                limit=query.limit,
            ),
        )

    def get_stats(self, limit: int = 10) -> StatsSummary:
        """Get occurrence totals and top term and source rankings."""
        return self._service.stats(limit)

    def edit_occurrence(
        self,
        occurrence_id: UUID,
        update: OccurrenceUpdate,
    ) -> OccurrenceItem:
        """Edit occurrence context using its stable UUID."""
        return self._service.edit_occurrence_by_public_id(occurrence_id, update)

    def add_tag(self, meaning_id: UUID, name: str) -> Meaning:
        """Add a tag to a meaning."""
        return self._service.add_tag(self._local_meaning_id(meaning_id), name)

    def remove_tag(self, meaning_id: UUID, name: str) -> Meaning:
        """Remove a tag from a meaning."""
        return self._service.remove_tag(self._local_meaning_id(meaning_id), name)

    def list_tags(self) -> list[TagSummary]:
        """List tags with their active meaning counts."""
        return self._service.tags()

    def favorite_meaning(self, meaning_id: UUID) -> Meaning:
        """Mark a meaning as a favorite."""
        return self._service.favorite_meaning(self._local_meaning_id(meaning_id))

    def unfavorite_meaning(self, meaning_id: UUID) -> Meaning:
        """Remove a meaning from favorites."""
        return self._service.unfavorite_meaning(self._local_meaning_id(meaning_id))

    def relate_meanings(self, meaning_id: UUID, related_id: UUID) -> list[Meaning]:
        """Create a symmetric relationship between two meanings."""
        return self._service.relate(
            self._local_meaning_id(meaning_id),
            self._local_meaning_id(related_id),
        )

    def unrelate_meanings(self, meaning_id: UUID, related_id: UUID) -> list[Meaning]:
        """Remove a relationship between two meanings."""
        return self._service.unrelate(
            self._local_meaning_id(meaning_id),
            self._local_meaning_id(related_id),
        )

    def list_related(self, meaning_id: UUID) -> list[Meaning]:
        """List active meanings related to one meaning."""
        return self._service.related(self._local_meaning_id(meaning_id))

    def add_reference(
        self,
        meaning_id: UUID,
        url: str,
        title: str | None = None,
    ) -> ReferenceLink:
        """Attach an HTTP or HTTPS reference URL to a meaning."""
        return self._service.add_reference(
            self._local_meaning_id(meaning_id),
            url,
            title,
        )

    def list_references(self, meaning_id: UUID) -> list[ReferenceLink]:
        """List reference URLs attached to a meaning."""
        return self._service.references(self._local_meaning_id(meaning_id))

    def _local_meaning_id(self, public_id: UUID) -> int:
        return self._service.get_meaning_by_public_id(public_id).meaning_id

    def _local_inbox_id(self, public_id: UUID) -> int:
        return self._service.get_inbox_by_public_id(public_id).inbox_id


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
    ):
        server.add_tool(tool, structured_output=True)
    return server


def main() -> None:
    """Run the local MCP server over the standard input/output transport."""
    create_server().run(transport="stdio")  # pragma: no cover - process boundary
