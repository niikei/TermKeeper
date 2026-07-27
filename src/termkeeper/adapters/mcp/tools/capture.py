"""Capture and inbox MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalCaptureBatchResult,
    ExternalCaptureResult,
    ExternalOccurrence,
    ExternalPage,
    inbox_search_query,
)
from termkeeper.adapters.mcp.inputs import CaptureBatchInput, InboxSearchFilters, Limit, Offset
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import CaptureInput


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

    def capture_terms(self, request: CaptureBatchInput) -> ExternalCaptureBatchResult:
        """Atomically capture 1-100 terms; duplicate or invalid input writes nothing."""
        return self._mapper.capture_batch(
            self._service.capture_many(
                tuple(
                    CaptureInput(
                        item.keyword,
                        item.memo,
                        item.source,
                        (
                            self._local_meaning_id(item.meaning_id)
                            if item.meaning_id is not None
                            else None
                        ),
                    )
                    for item in request.items
                ),
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

    def search_inbox(
        self,
        query: InboxSearchFilters,
    ) -> ExternalPage[ExternalOccurrence]:
        """Search unresolved occurrences only; use this for pending classification work."""
        return self._mapper.occurrence_page(
            self._service.search_inbox(inbox_search_query(query)),
        )
