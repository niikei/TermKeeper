"""Inbox HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import FastAPI, Query, status

from termkeeper.adapters.external import (
    ExternalAddResult,
    ExternalInbox,
    ExternalMapper,
    ExternalMeaning,
    ExternalPage,
    page,
)
from termkeeper.adapters.http.common import _local_inbox_id
from termkeeper.adapters.http.requests import CaptureRequest, ResolveRequest
from termkeeper.application import TermKeeperService


def _register_inbox_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register capture and resolution routes."""

    @app.post("/api/v1/inbox", status_code=status.HTTP_201_CREATED)
    def capture(request: CaptureRequest) -> ExternalAddResult:
        return mapper.add_result(service.add(request.keyword, request.memo, request.source))

    @app.get("/api/v1/inbox")
    def inbox(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalInbox]:
        return page([mapper.inbox(item) for item in service.inbox()], offset, limit)

    @app.post("/api/v1/inbox/{inbox_id}/resolve")
    def resolve(inbox_id: UUID, request: ResolveRequest) -> ExternalMeaning:
        return mapper.meaning(
            service.resolve(
                _local_inbox_id(service, inbox_id),
                request.full_name,
                request.description,
            ),
        )
