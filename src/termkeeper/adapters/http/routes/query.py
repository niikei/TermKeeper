"""Search and analytics HTTP routes."""

from typing import Annotated

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalSearchResult
from termkeeper.adapters.http.requests import SearchFilters
from termkeeper.application import TermKeeperService
from termkeeper.domain import SearchField, SearchQuery, StatsSummary


def _register_query_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register search and analytics routes."""

    @app.get("/api/v1/search")
    def search(
        filters: Annotated[SearchFilters, Query()],
    ) -> ExternalSearchResult:
        query = SearchQuery(
            text=filters.text,
            field=SearchField(filters.field),
            tag=filters.tag,
            scope=filters.scope,
            favorite_only=filters.favorite_only,
            limit=filters.offset + filters.limit + 1,
        )
        return mapper.search_result(
            service.search(query),
            offset=filters.offset,
            limit=filters.limit,
        )

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> StatsSummary:
        return service.stats(limit)
