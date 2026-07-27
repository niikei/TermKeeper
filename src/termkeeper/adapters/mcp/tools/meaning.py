"""AI-oriented Meaning lifecycle MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalMeaning, ExternalPage
from termkeeper.adapters.mcp.inputs import (
    Limit,
    MeaningCreateInput,
    MeaningEditInput,
    NonEmptyText,
    Offset,
)
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import PageQuery


class MeaningTools(ToolContext):
    def create_meaning(self, request: MeaningCreateInput) -> ExternalMeaning:
        """Create a scoped meaning after search_meanings confirms it is not a duplicate."""
        return self._mapper.meaning(
            self._service.create_meaning(
                request.full_name,
                request.description,
                request.aliases,
                self._scope_name(request.scope_id),
            ),
        )

    def edit_meaning(
        self,
        meaning_id: UUID,
        request: MeaningEditInput,
    ) -> ExternalMeaning:
        """Replace a meaning's name, scope, and optional description."""
        return self._mapper.meaning(
            self._service.edit(
                self._local_meaning_id(meaning_id),
                request.full_name,
                request.description,
                self._scope_name(request.scope_id),
            ),
        )

    def add_alias(self, meaning_id: UUID, alias: NonEmptyText) -> ExternalMeaning:
        """Add a searchable alias to an active meaning."""
        return self._mapper.meaning(
            self._service.add_alias(self._local_meaning_id(meaning_id), alias),
        )

    def remove_alias(self, meaning_id: UUID, alias: NonEmptyText) -> ExternalMeaning:
        """Remove one alias from an active meaning."""
        return self._mapper.meaning(
            self._service.remove_alias(self._local_meaning_id(meaning_id), alias),
        )

    def delete_meaning(self, meaning_id: UUID) -> dict[str, UUID]:
        """Soft-delete a meaning; use restore_meaning to undo this action."""
        self._service.delete_meaning(self._local_meaning_id(meaning_id))
        return {"meaning_id": meaning_id}

    def list_trash(
        self,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalMeaning]:
        """List soft-deleted meanings available for restoration."""
        return self._mapper.meaning_page(
            self._service.trash_page(PageQuery(offset, limit)),
        )

    def restore_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Restore a soft-deleted meaning when its scoped name remains unique."""
        local_id = self._service.get_meaning_by_public_id(
            meaning_id,
            include_deleted=True,
        ).meaning_id
        return self._mapper.meaning(self._service.restore_meaning(local_id))
