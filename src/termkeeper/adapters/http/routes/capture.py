"""Occurrence capture and pending inbox HTTP routes."""

from typing import Annotated

from fastapi import FastAPI, Query, status

from termkeeper.adapters.external import (
    ExternalCaptureBatchResult,
    ExternalCaptureResult,
    ExternalMapper,
    ExternalOccurrence,
    ExternalPage,
    inbox_search_query,
)
from termkeeper.adapters.http.common import _local_meaning_id
from termkeeper.adapters.http.requests import (
    CaptureBatchRequest,
    CaptureRequest,
    InboxSearchFilters,
)
from termkeeper.application import TermKeeperService
from termkeeper.domain import CaptureInput


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

    @app.post("/api/v1/occurrences/batch", status_code=status.HTTP_201_CREATED)
    def capture_batch(request: CaptureBatchRequest) -> ExternalCaptureBatchResult:
        return mapper.capture_batch(
            service.capture_many(
                tuple(
                    CaptureInput(
                        item.keyword,
                        item.memo,
                        item.source,
                        (
                            _local_meaning_id(service, item.meaning_id)
                            if item.meaning_id is not None
                            else None
                        ),
                    )
                    for item in request.items
                ),
            ),
        )

    @app.get("/api/v1/inbox")
    def inbox(
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalOccurrence]:
        return mapper.occurrence_page(service.inbox(offset=offset, limit=limit))

    @app.get("/api/v1/inbox/search")
    def search_inbox(
        filters: Annotated[InboxSearchFilters, Query()],
    ) -> ExternalPage[ExternalOccurrence]:
        return mapper.occurrence_page(
            service.search_inbox(inbox_search_query(filters)),
        )
