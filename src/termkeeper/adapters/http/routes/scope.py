"""Meaning scope HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query, Response, status

from termkeeper.adapters.external import ExternalMapper, ExternalPage, ExternalScope, page
from termkeeper.adapters.http.requests import ScopeCreateRequest, ScopeUpdateRequest
from termkeeper.application import TermKeeperService


def _register_scope_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    @app.get("/api/v1/scopes")
    def list_scopes(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalScope]:
        return page([mapper.scope(item) for item in service.scopes()], offset, limit)

    @app.post("/api/v1/scopes", status_code=status.HTTP_201_CREATED)
    def create_scope(request: ScopeCreateRequest) -> ExternalScope:
        return mapper.scope(service.create_scope(request.name, request.description))

    @app.put("/api/v1/scopes/{scope_id}")
    def edit_scope(scope_id: UUID, request: ScopeUpdateRequest) -> ExternalScope:
        local_id = service.get_scope_by_public_id(scope_id).scope_id
        return mapper.scope(service.edit_scope(local_id, request.name, request.description))

    @app.delete("/api/v1/scopes/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_scope(scope_id: UUID) -> Response:
        local_id = service.get_scope_by_public_id(scope_id).scope_id
        service.delete_scope(local_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
