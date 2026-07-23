"""Search and analytics HTTP routes."""

from typing import Annotated

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalSearchResult
from termkeeper.adapters.http.common import _scope_name
from termkeeper.adapters.http.requests import SearchFilters
from termkeeper.application import TermKeeperService
from termkeeper.domain import SearchField, SearchQuery, StatsSummary


def meaning_search_result(
    filters: SearchFilters,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> ExternalSearchResult:
    query = SearchQuery(
        text=filters.text,
        field=SearchField(filters.field),
        tag=filters.tag,
        scope=(
            _scope_name(service, filters.scope_id)
            if filters.scope_id is not None
            else None
        ),
        favorite_only=filters.favorite_only,
        offset=filters.offset,
        limit=filters.limit,
    )
    return mapper.search_result(service.search_meanings(query))


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
        return meaning_search_result(filters, service, mapper)

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> StatsSummary:
        return service.stats(limit)
