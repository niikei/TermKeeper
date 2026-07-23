"""Occurrence capture and pending inbox HTTP routes."""

from typing import Annotated

from fastapi import FastAPI, Query, status

from termkeeper.adapters.external import (
    ExternalCaptureResult,
    ExternalMapper,
    ExternalOccurrence,
    ExternalPage,
)
from termkeeper.adapters.http.common import _local_meaning_id
from termkeeper.adapters.http.requests import CaptureRequest
from termkeeper.application import TermKeeperService


def _register_capture_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register capture and resolution routes."""

    @app.post("/api/v1/occurrences", status_code=status.HTTP_201_CREATED)
    def capture(request: CaptureRequest) -> ExternalCaptureResult:
        meaning_id = (
            _local_meaning_id(service, request.meaning_id)
            if request.meaning_id is not None
            else None
        )
        return mapper.capture_result(
            service.add(
                request.keyword,
                request.memo,
                request.source,
                meaning_id=meaning_id,
            ),
        )

    @app.get("/api/v1/inbox")
    def inbox(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalOccurrence]:
        return mapper.occurrence_page(service.inbox(offset=offset, limit=limit))
