"""Meaning relation HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalMeaning, ExternalPage, page
from termkeeper.adapters.http.common import _local_meaning_id
from termkeeper.application import TermKeeperService


def _register_relation_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    @app.get("/api/v1/meanings/{meaning_id}/related")
    def related(
        meaning_id: UUID,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalMeaning]:
        return page(
            [
                mapper.meaning(item)
                for item in service.related(_local_meaning_id(service, meaning_id))
            ],
            offset,
            limit,
        )

    @app.put("/api/v1/meanings/{meaning_id}/related/{related_id}")
    def relate(meaning_id: UUID, related_id: UUID) -> list[ExternalMeaning]:
        return [
            mapper.meaning(item)
            for item in service.relate(
                _local_meaning_id(service, meaning_id),
                _local_meaning_id(service, related_id),
            )
        ]

    @app.delete("/api/v1/meanings/{meaning_id}/related/{related_id}")
    def unrelate(meaning_id: UUID, related_id: UUID) -> list[ExternalMeaning]:
        return [
            mapper.meaning(item)
            for item in service.unrelate(
                _local_meaning_id(service, meaning_id),
                _local_meaning_id(service, related_id),
            )
        ]
