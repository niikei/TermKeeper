"""Reference MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalPage, ExternalReference, page
from termkeeper.adapters.mcp.inputs import Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import ReferenceUpdate


class ReferenceTools(ToolContext):
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
            self._mapper.references(
                self._service.references(self._local_meaning_id(meaning_id)),
            ),
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
