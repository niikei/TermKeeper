"""Capture and inbox MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalCaptureResult,
    ExternalOccurrence,
    ExternalPage,
)
from termkeeper.adapters.mcp.inputs import Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext


class CaptureTools(ToolContext):
    def capture_term(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
        meaning_id: UUID | None = None,
    ) -> ExternalCaptureResult:
        """Capture a term now and preserve where it was encountered."""
        local_meaning_id = self._local_meaning_id(meaning_id) if meaning_id is not None else None
        return self._mapper.capture_result(
            self._service.add(
                keyword,
                memo,
                source,
                meaning_id=local_meaning_id,
            ),
        )

    def list_inbox(
        self,
        offset: Offset = 0,
        limit: Limit = 20,
    ) -> ExternalPage[ExternalOccurrence]:
        """List unresolved captured terms."""
        return self._mapper.occurrence_page(
            self._service.inbox(offset=offset, limit=limit),
        )
