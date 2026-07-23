"""Meaning scope MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalPage, ExternalScope, page
from termkeeper.adapters.mcp.inputs import Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext


class ScopeTools(ToolContext):
    def create_scope(self, name: str, description: str | None = None) -> ExternalScope:
        """Create a controlled meaning namespace."""
        return self._mapper.scope(self._service.create_scope(name, description))

    def list_scopes(
        self,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalScope]:
        """List configured meaning scopes."""
        return page([self._mapper.scope(item) for item in self._service.scopes()], offset, limit)

    def edit_scope(
        self,
        scope_id: UUID,
        name: str,
        description: str | None = None,
    ) -> ExternalScope:
        """Edit a scope using its stable UUID."""
        local_id = self._service.get_scope_by_public_id(scope_id).scope_id
        return self._mapper.scope(self._service.edit_scope(local_id, name, description))

    def delete_scope(self, scope_id: UUID) -> dict[str, UUID]:
        """Delete an unused non-default scope."""
        local_id = self._service.get_scope_by_public_id(scope_id).scope_id
        self._service.delete_scope(local_id)
        return {"scope_id": scope_id}
