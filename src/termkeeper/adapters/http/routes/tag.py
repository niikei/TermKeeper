"""Tag and favorite HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query

from termkeeper.adapters.external import ExternalMapper, ExternalMeaning, ExternalPage, page
from termkeeper.adapters.http.common import _local_meaning_id
from termkeeper.application import TermKeeperService
from termkeeper.domain import TagSummary


def _register_tag_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    @app.get("/api/v1/tags")
    def list_tags(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[TagSummary]:
        return page(service.tags(), offset, limit)

    @app.put("/api/v1/meanings/{meaning_id}/tags/{name}")
    def add_tag(meaning_id: UUID, name: str) -> ExternalMeaning:
        return mapper.meaning(
            service.add_tag(_local_meaning_id(service, meaning_id), name),
        )

    @app.delete("/api/v1/meanings/{meaning_id}/tags/{name}")
    def remove_tag(meaning_id: UUID, name: str) -> ExternalMeaning:
        return mapper.meaning(
            service.remove_tag(_local_meaning_id(service, meaning_id), name),
        )

    @app.put("/api/v1/meanings/{meaning_id}/favorite")
    def favorite(meaning_id: UUID) -> ExternalMeaning:
        return mapper.meaning(
            service.favorite_meaning(_local_meaning_id(service, meaning_id)),
        )

    @app.delete("/api/v1/meanings/{meaning_id}/favorite")
    def unfavorite(meaning_id: UUID) -> ExternalMeaning:
        return mapper.meaning(
            service.unfavorite_meaning(_local_meaning_id(service, meaning_id)),
        )
