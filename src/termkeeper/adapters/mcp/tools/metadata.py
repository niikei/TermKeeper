"""Tag, favorite, and relation MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalMeaning, ExternalPage, page
from termkeeper.adapters.mcp.inputs import Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import TagSummary


class MetadataTools(ToolContext):
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
