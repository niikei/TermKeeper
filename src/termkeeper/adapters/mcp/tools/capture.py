"""Capture and inbox MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalAddResult,
    ExternalInbox,
    ExternalMeaning,
    ExternalPage,
    page,
)
from termkeeper.adapters.mcp.inputs import Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext


class CaptureTools(ToolContext):
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
