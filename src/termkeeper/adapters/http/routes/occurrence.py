"""Occurrence HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalOccurrence, ExternalPage, page
from termkeeper.adapters.http.common import _local_inbox_id, _local_meaning_id
from termkeeper.adapters.http.requests import OccurrenceFilters, OccurrenceUpdateRequest
from termkeeper.application import TermKeeperService
from termkeeper.domain import OccurrenceQuery, OccurrenceUpdate


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
        inbox_id = (
            _local_inbox_id(service, filters.inbox_id) if filters.inbox_id is not None else None
        )
        items = [
            mapper.occurrence(item)
            for item in service.occurrences(
                OccurrenceQuery(
                    meaning_id=meaning_id,
                    inbox_id=inbox_id,
                    keyword=filters.keyword,
                    source=filters.source,
                    since=filters.since,
                    limit=filters.offset + filters.limit + 1,
                ),
            )
        ]
        return page(items, filters.offset, filters.limit)

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
