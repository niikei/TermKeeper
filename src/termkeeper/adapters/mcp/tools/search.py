"""Search and analytics MCP tools."""

from uuid import UUID

from termkeeper.adapters.external import ExternalMeaning, ExternalSearchResult
from termkeeper.adapters.mcp.inputs import SearchFilters
from termkeeper.adapters.mcp.tools.context import ToolContext
from termkeeper.domain import SearchField, SearchQuery, StatsSummary


class SearchTools(ToolContext):
    def search_meanings(
        self,
        query: SearchFilters,
    ) -> ExternalSearchResult:
        """Search meanings and return ranked hits or similar suggestions."""
        domain_query = SearchQuery(
            text=query.text,
            field=SearchField(query.field),
            limit=query.offset + query.limit + 1,
            tag=query.tag,
            scope=query.scope,
            favorite_only=query.favorite_only,
        )
        return self._mapper.search_result(
            self._service.search(domain_query),
            offset=query.offset,
            limit=query.limit,
        )

    def get_meaning(self, meaning_id: UUID) -> ExternalMeaning:
        """Get one active meaning by its stable UUID."""
        return self._mapper.meaning(self._service.get_meaning_by_public_id(meaning_id))

    def get_stats(self, limit: int = 10) -> StatsSummary:
        """Get occurrence totals and top term and source rankings."""
        return self._service.stats(limit)
