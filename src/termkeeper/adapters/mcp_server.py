"""Model Context Protocol adapter backed by TermKeeperService."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from termkeeper.adapters.models import (
    ExternalAddResult,
    ExternalInbox,
    ExternalMapper,
    ExternalMeaning,
    ExternalOccurrence,
    ExternalPage,
    ExternalReference,
    ExternalSearchResult,
    page,
)
from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    OccurrenceQuery,
    OccurrenceUpdate,
    ReferenceUpdate,
    SearchField,
    SearchQuery,
    StatsSummary,
    TagSummary,
)

type Offset = Annotated[int, Field(ge=0, le=399)]
type Limit = Annotated[int, Field(ge=1, le=100)]


@dataclass(frozen=True)
class OccurrenceFilters:
    meaning_id: UUID | None = None
    inbox_id: UUID | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    offset: Offset = 0
    limit: Limit = 50


@dataclass(frozen=True)
class SearchFilters:
    text: str
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    favorite_only: bool = False
    offset: Offset = 0
    limit: Limit = 20


class TermKeeperMcpTools:
    """Typed MCP-facing operations with no protocol or persistence logic."""

    def __init__(self, service: TermKeeperService) -> None:
        self._service = service
        self._mapper = ExternalMapper(service)

    def capture_term(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
    ) -> ExternalAddResult:
        """Capture a term now and preserve where it was encountered."""
        return self._mapper.add_result(self._service.add(keyword, memo, source))

    def list_inbox(
        self,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalInbox]:
        """List unresolved captured terms."""
        return page(
            [self._mapper.inbox(item) for item in self._service.inbox()],
            offset,
            limit,
        )

    def resolve_inbox(
        self,
        inbox_id: UUID,
        full_name: str,
        description: str | None = None,
    ) -> ExternalMeaning:
        """Resolve an inbox item into a searchable meaning."""
        return self._mapper.meaning(
            self._service.resolve(
                self._local_inbox_id(inbox_id),
                full_name,
                description,
            ),
        )

    def search_meanings(
        self,
        query: SearchFilters,
    ) -> ExternalSearchResult:
        """Search meanings and return ranked hits or similar suggestions."""
        domain_query = SearchQuery(
            text=query.text,
            field=SearchField(query.field),
            limit=query.offset + query.limit + 1,
            tag=query.tag,
            favorite_only=query.favorite_only,
        )
        return self._mapper.search_result(
            self._service.search(domain_query),
            offset=query.offset,
            limit=query.limit,
        )

    def get_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Get one active meaning by its stable UUID."""
        return self._mapper.meaning(self._service.get_meaning_by_public_id(meaning_id))

    def list_occurrences(
        self,
        query: OccurrenceFilters | None = None,
    ) -> ExternalPage[ExternalOccurrence]:
        """List encounter history with optional filters."""
        query = query or OccurrenceFilters()
        meaning_id = (
            self._local_meaning_id(query.meaning_id, include_deleted=True)
            if query.meaning_id is not None
            else None
        )
        inbox_id = self._local_inbox_id(query.inbox_id) if query.inbox_id is not None else None
        items = [
            self._mapper.occurrence(item)
            for item in self._service.occurrences(
                OccurrenceQuery(
                    meaning_id=meaning_id,
                    inbox_id=inbox_id,
                    keyword=query.keyword,
                    source=query.source,
                    since=query.since,
                    limit=query.offset + query.limit + 1,
                ),
            )
        ]
        return page(items, query.offset, query.limit)

    def get_stats(self, limit: int = 10) -> StatsSummary:
        """Get occurrence totals and top term and source rankings."""
        return self._service.stats(limit)

    def edit_occurrence(
        self,
        occurrence_id: UUID,
        update: OccurrenceUpdate,
    ) -> ExternalOccurrence:
        """Edit occurrence context using its stable UUID."""
        return self._mapper.occurrence(
            self._service.edit_occurrence_by_public_id(occurrence_id, update),
        )

    def add_tag(self, meaning_id: UUID, name: str) -> ExternalMeaning:
        """Add a tag to a meaning."""
        return self._mapper.meaning(
            self._service.add_tag(self._local_meaning_id(meaning_id), name),
        )

    def remove_tag(self, meaning_id: UUID, name: str) -> ExternalMeaning:
        """Remove a tag from a meaning."""
        return self._mapper.meaning(
            self._service.remove_tag(self._local_meaning_id(meaning_id), name),
        )

    def list_tags(
        self,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[TagSummary]:
        """List tags with their active meaning counts."""
        return page(self._service.tags(), offset, limit)

    def favorite_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Mark a meaning as a favorite."""
        return self._mapper.meaning(
            self._service.favorite_meaning(self._local_meaning_id(meaning_id)),
        )

    def unfavorite_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Remove a meaning from favorites."""
        return self._mapper.meaning(
            self._service.unfavorite_meaning(self._local_meaning_id(meaning_id)),
        )

    def relate_meanings(
        self,
        meaning_id: UUID,
        related_id: UUID,
    ) -> list[ExternalMeaning]:
        """Create a symmetric relationship between two meanings."""
        return [
            self._mapper.meaning(item)
            for item in self._service.relate(
                self._local_meaning_id(meaning_id),
                self._local_meaning_id(related_id),
            )
        ]

    def unrelate_meanings(
        self,
        meaning_id: UUID,
        related_id: UUID,
    ) -> list[ExternalMeaning]:
        """Remove a relationship between two meanings."""
        return [
            self._mapper.meaning(item)
            for item in self._service.unrelate(
                self._local_meaning_id(meaning_id),
                self._local_meaning_id(related_id),
            )
        ]

    def list_related(
        self,
        meaning_id: UUID,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalMeaning]:
        """List active meanings related to one meaning."""
        return page(
            [
                self._mapper.meaning(item)
                for item in self._service.related(self._local_meaning_id(meaning_id))
            ],
            offset,
            limit,
        )

    def add_reference(
        self,
        meaning_id: UUID,
        url: str,
        title: str | None = None,
    ) -> ExternalReference:
        """Attach an HTTP or HTTPS reference URL to a meaning."""
        return self._mapper.reference(
            self._service.add_reference(
                self._local_meaning_id(meaning_id),
                url,
                title,
            ),
        )

    def list_references(
        self,
        meaning_id: UUID,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalReference]:
        """List reference URLs attached to a meaning."""
        return page(
            [
                self._mapper.reference(item)
                for item in self._service.references(self._local_meaning_id(meaning_id))
            ],
            offset,
            limit,
        )

    def edit_reference(
        self,
        reference_id: UUID,
        update: ReferenceUpdate,
    ) -> ExternalReference:
        """Edit a reference using its stable UUID."""
        return self._mapper.reference(
            self._service.edit_reference(reference_id, update),
        )

    def remove_reference(self, reference_id: UUID) -> ExternalReference:
        """Remove a reference using its stable UUID."""
        return self._mapper.reference(self._service.remove_reference(reference_id))

    def _local_meaning_id(
        self,
        public_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> int:
        return self._service.get_meaning_by_public_id(
            public_id,
            include_deleted=include_deleted,
        ).meaning_id

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
        tools.edit_reference,
        tools.remove_reference,
    ):
        server.add_tool(tool, structured_output=True)
    return server


def main() -> None:
    """Run the local MCP server over the standard input/output transport."""
    create_server().run(transport="stdio")  # pragma: no cover - process boundary
