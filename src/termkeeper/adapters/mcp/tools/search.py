"""Search and analytics MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import (
    ExternalMeaning,
    ExternalPage,
    ExternalSearchResult,
    meaning_search_query,
)
from termkeeper.adapters.mcp.inputs import MeaningFilters, SearchFilters
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import MeaningListQuery, StatsSummary


class SearchTools(ToolContext):
    def list_meanings(
        self,
        query: MeaningFilters | None = None,
    ) -> ExternalPage[ExternalMeaning]:
        """List known meanings without search text; follow has_more for the next page."""
        query = query or MeaningFilters()
        scope = self._scope_name(query.scope_id) if query.scope_id is not None else None
        return self._mapper.meaning_page(
            self._service.meaning_page(
                MeaningListQuery(
                    tag=query.tag,
                    scope=scope,
                    favorite_only=query.favorite_only,
                    offset=query.offset,
                    limit=query.limit,
                ),
            ),
        )

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
