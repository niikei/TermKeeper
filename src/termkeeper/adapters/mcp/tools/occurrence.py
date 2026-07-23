"""Occurrence MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalOccurrence, ExternalPage, page
from termkeeper.adapters.mcp.inputs import OccurrenceFilters
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import OccurrenceQuery, OccurrenceUpdate


class OccurrenceTools(ToolContext):
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

    def edit_occurrence(
        self,
        occurrence_id: UUID,
        update: OccurrenceUpdate,
    ) -> ExternalOccurrence:
        """Edit occurrence context using its stable UUID."""
        return self._mapper.occurrence(
            self._service.edit_occurrence_by_public_id(occurrence_id, update),
        )
