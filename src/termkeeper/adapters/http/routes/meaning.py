"""Meaning lifecycle HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query, Response, status

from termkeeper.adapters.external import (
    ExternalMapper,
    ExternalMeaning,
    ExternalPage,
    ExternalSearchResult,
    meaning_search_query,
    page,
)
from termkeeper.adapters.http.common import _local_meaning_id, _scope_name
from termkeeper.adapters.http.requests import MeaningUpdateRequest, SearchFilters
from termkeeper.application import TermKeeperService
from termkeeper.domain import MeaningListQuery


def _register_meaning_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register meaning lifecycle routes."""

    @app.get("/api/v1/meanings/search")
    def search_meanings(
        filters: Annotated[SearchFilters, Query()],
    ) -> ExternalSearchResult:
        return mapper.search_result(
            service.search_meanings(meaning_search_query(service, filters)),
        )

    @app.get("/api/v1/meanings/{meaning_id}")
    def get_meaning(meaning_id: UUID) -> ExternalMeaning:
        return mapper.meaning(service.get_meaning_by_public_id(meaning_id))

    @app.get("/api/v1/meanings")
    def list_meanings(
        tag: str | None = None,
        *,
        scope_id: UUID | None = None,
        favorite_only: bool = False,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalMeaning]:
        return mapper.meaning_page(
            service.meaning_page(
                MeaningListQuery(
                    tag=tag,
                    scope=(_scope_name(service, scope_id) if scope_id is not None else None),
                    favorite_only=favorite_only,
                    offset=offset,
                    limit=limit,
                ),
            ),
        )

    @app.put("/api/v1/meanings/{meaning_id}")
    def update_meaning(
        meaning_id: UUID,
        request: MeaningUpdateRequest,
    ) -> ExternalMeaning:
        return mapper.meaning(
            service.edit(
                _local_meaning_id(service, meaning_id),
                request.full_name,
                request.description,
                _scope_name(service, request.scope_id),
            ),
        )

    @app.delete(
        "/api/v1/meanings/{meaning_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_meaning(meaning_id: UUID) -> Response:
        service.delete_meaning(_local_meaning_id(service, meaning_id))
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/trash")
    def list_trash(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalMeaning]:
        return page([mapper.meaning(item) for item in service.trash()], offset, limit)

    @app.post("/api/v1/trash/{meaning_id}/restore")
    def restore_meaning(meaning_id: UUID) -> ExternalMeaning:
        local_id = _local_meaning_id(service, meaning_id, include_deleted=True)
        return mapper.meaning(service.restore_meaning(local_id))
