"""Occurrence HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query

from termkeeper.adapters.external import (
    ExternalMapper,
    ExternalMeaning,
    ExternalOccurrence,
    ExternalPage,
)
from termkeeper.adapters.http.common import (
    _local_meaning_id,
    _local_occurrence_id,
    _scope_name,
)
from termkeeper.adapters.http.requests import (
    OccurrenceFilters,
    OccurrenceUpdateRequest,
    ResolveRequest,
)
from termkeeper.application import TermKeeperService
from termkeeper.domain import OccurrenceQuery, OccurrenceStatus, OccurrenceUpdate


def _register_occurrence_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    @app.get("/api/v1/occurrences")
    def list_occurrences(
        filters: Annotated[OccurrenceFilters, Query()],
    ) -> ExternalPage[ExternalOccurrence]:
        meaning_id = (
            _local_meaning_id(service, filters.meaning_id, include_deleted=True)
            if filters.meaning_id is not None
            else None
        )
        return mapper.occurrence_page(
            service.occurrences(
                OccurrenceQuery(
                    meaning_id=meaning_id,
                    status=OccurrenceStatus(filters.status) if filters.status else None,
                    keyword=filters.keyword,
                    source=filters.source,
                    since=filters.since,
                    offset=filters.offset,
                    limit=filters.limit,
                ),
            ),
        )

    @app.put("/api/v1/occurrences/{occurrence_id}")
    def edit_occurrence(
        occurrence_id: UUID,
        request: OccurrenceUpdateRequest,
    ) -> ExternalOccurrence:
        return mapper.occurrence(
            service.edit_occurrence_by_public_id(
                occurrence_id,
                OccurrenceUpdate(**request.model_dump()),
            ),
        )

    @app.post("/api/v1/occurrences/{occurrence_id}/resolve")
    def resolve_occurrence(
        occurrence_id: UUID,
        request: ResolveRequest,
    ) -> ExternalMeaning:
        return mapper.meaning(
            service.resolve(
                _local_occurrence_id(service, occurrence_id),
                request.full_name,
                request.description,
                _scope_name(service, request.scope_id),
            ),
        )

    @app.post("/api/v1/occurrences/{occurrence_id}/assign/{meaning_id}")
    def assign_occurrence(occurrence_id: UUID, meaning_id: UUID) -> ExternalOccurrence:
        return mapper.occurrence(
            service.assign(
                _local_occurrence_id(service, occurrence_id),
                _local_meaning_id(service, meaning_id),
            ),
        )

    @app.post("/api/v1/occurrences/{occurrence_id}/unresolve")
    def unresolve_occurrence(occurrence_id: UUID) -> ExternalOccurrence:
        return mapper.occurrence(
            service.unresolve(_local_occurrence_id(service, occurrence_id)),
        )

    @app.post("/api/v1/occurrences/{occurrence_id}/discard")
    def discard_occurrence(occurrence_id: UUID) -> ExternalOccurrence:
        return mapper.occurrence(
            service.discard(_local_occurrence_id(service, occurrence_id)),
        )

    @app.post("/api/v1/occurrences/{occurrence_id}/reopen")
    def reopen_occurrence(occurrence_id: UUID) -> ExternalOccurrence:
        return mapper.occurrence(
            service.reopen(_local_occurrence_id(service, occurrence_id)),
        )
