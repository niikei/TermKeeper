"""Occurrence MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalMeaning,
    ExternalOccurrence,
    ExternalPage,
)
from termkeeper.adapters.mcp.inputs import OccurrenceFilters
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import OccurrenceQuery, OccurrenceStatus, OccurrenceUpdate


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
        return self._mapper.occurrence_page(
            self._service.occurrences(
                OccurrenceQuery(
                    meaning_id=meaning_id,
                    status=OccurrenceStatus(query.status) if query.status else None,
                    keyword=query.keyword,
                    source=query.source,
                    since=query.since,
                    offset=query.offset,
                    limit=query.limit,
                ),
            ),
        )

    def edit_occurrence(
        self,
        occurrence_id: UUID,
        update: OccurrenceUpdate,
    ) -> ExternalOccurrence:
        """Edit occurrence context using its stable UUID."""
        return self._mapper.occurrence(
            self._service.edit_occurrence_by_public_id(occurrence_id, update),
        )

    def resolve_occurrence(
        self,
        occurrence_id: UUID,
        full_name: str,
        scope: str = "General",
        description: str | None = None,
    ) -> ExternalMeaning:
        """Create a scoped meaning and classify one pending occurrence."""
        return self._mapper.meaning(
            self._service.resolve(
                self._local_occurrence_id(occurrence_id),
                full_name,
                description,
                scope,
            ),
        )

    def assign_occurrence(
        self,
        occurrence_id: UUID,
        meaning_id: UUID,
    ) -> ExternalOccurrence:
        """Classify or reclassify an occurrence to an explicit meaning."""
        return self._mapper.occurrence(
            self._service.assign(
                self._local_occurrence_id(occurrence_id),
                self._local_meaning_id(meaning_id),
            ),
        )

    def unresolve_occurrence(self, occurrence_id: UUID) -> ExternalOccurrence:
        """Return a resolved occurrence to the pending inbox."""
        return self._mapper.occurrence(
            self._service.unresolve(self._local_occurrence_id(occurrence_id)),
        )

    def discard_occurrence(self, occurrence_id: UUID) -> ExternalOccurrence:
        """Discard a pending occurrence."""
        return self._mapper.occurrence(
            self._service.discard(self._local_occurrence_id(occurrence_id)),
        )

    def reopen_occurrence(self, occurrence_id: UUID) -> ExternalOccurrence:
        """Return a discarded occurrence to the pending inbox."""
        return self._mapper.occurrence(
            self._service.reopen(self._local_occurrence_id(occurrence_id)),
        )
