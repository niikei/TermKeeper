"""Meaning reference HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalPage, ExternalReference
from termkeeper.adapters.http.common import _local_meaning_id
from termkeeper.adapters.http.requests import ReferenceCreateRequest, ReferenceUpdateRequest
from termkeeper.application import TermKeeperService
from termkeeper.domain import PageQuery, ReferenceUpdate


def _register_reference_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    @app.get("/api/v1/meanings/{meaning_id}/references")
    def references(
        meaning_id: UUID,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalReference]:
        return mapper.reference_page(
            service.reference_page(
                _local_meaning_id(service, meaning_id),
                PageQuery(offset, limit),
            ),
        )

    @app.post("/api/v1/meanings/{meaning_id}/references")
    def add_reference(
        meaning_id: UUID,
        request: ReferenceCreateRequest,
    ) -> ExternalReference:
        return mapper.reference(
            service.add_reference(
                _local_meaning_id(service, meaning_id),
                request.url,
                request.title,
            ),
        )

    @app.put("/api/v1/references/{reference_id}")
    def edit_reference(
        reference_id: UUID,
        request: ReferenceUpdateRequest,
    ) -> ExternalReference:
        return mapper.reference(
            service.edit_reference(
                reference_id,
                ReferenceUpdate(**request.model_dump()),
            ),
        )

    @app.delete("/api/v1/references/{reference_id}")
    def remove_reference(reference_id: UUID) -> ExternalReference:
        return mapper.reference(service.remove_reference(reference_id))
