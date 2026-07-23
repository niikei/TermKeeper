"""Search and analytics MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalMeaning,
    ExternalSearchResult,
    meaning_search_query,
)
from termkeeper.adapters.mcp.inputs import SearchFilters
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import StatsSummary


class SearchTools(ToolContext):
    def search_meanings(
        self,
        query: SearchFilters,
    ) -> ExternalSearchResult:
        """Search known meanings. Follow has_more with offset + returned hit count."""
        return self._mapper.search_result(
            self._service.search_meanings(
                meaning_search_query(self._service, query),
            ),
        )

    def get_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Get one active meaning by its stable UUID."""
        return self._mapper.meaning(self._service.get_meaning_by_public_id(meaning_id))

    def get_stats(self, limit: int = 10) -> StatsSummary:
        """Get occurrence totals and top term and source rankings."""
        return self._service.stats(limit)
