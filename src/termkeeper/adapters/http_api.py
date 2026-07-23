"""HTTP API adapter backed by TermKeeperService."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

import uvicorn
from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from termkeeper.adapters.models import (
    ExternalAddResult,
    ExternalInbox,
    ExternalMapper,
    ExternalMeaning,
    ExternalOccurrence,
    ExternalPage,
    ExternalReference,
    ExternalSearchResult,
    page,
)
from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import (
    OccurrenceQuery,
    OccurrenceUpdate,
    ReferenceUpdate,
    SearchField,
    SearchQuery,
    StatsSummary,
    TagSummary,
)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ErrorResponse(BaseModel):
    error: str
    message: str


class CaptureRequest(BaseModel):
    keyword: str
    memo: str | None = None
    source: str | None = None


class ResolveRequest(BaseModel):
    full_name: str
    description: str | None = None


class MeaningUpdateRequest(BaseModel):
    full_name: str
    description: str | None = None


class OccurrenceFilters(BaseModel):
    meaning_id: UUID | None = None
    inbox_id: UUID | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    offset: int = Field(default=0, ge=0, le=399)
    limit: int = Field(default=50, ge=1, le=100)


class SearchFilters(BaseModel):
    text: str = Field(min_length=1)
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    favorite_only: bool = False
    offset: int = Field(default=0, ge=0, le=399)
    limit: int = Field(default=20, ge=1, le=100)


class OccurrenceUpdateRequest(BaseModel):
    keyword: str | None = None
    memo: str | None = None
    source: str | None = None
    clear_memo: bool = False
    clear_source: bool = False


class ReferenceCreateRequest(BaseModel):
    url: str
    title: str | None = None


class ReferenceUpdateRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    clear_title: bool = False


def create_app(service: TermKeeperService | None = None) -> FastAPI:
    """Create an API app without import-time database side effects."""
    if service is None:
        service = TermKeeperService()
        service.initialize()

    app = FastAPI(
        title="TermKeeper API",
        version="1.0.0",
        description="Capture unfamiliar terms and organize searchable meanings.",
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        },
    )
    _register_error_handlers(app)
    _register_system_routes(app, service)
    mapper = ExternalMapper(service)
    _register_inbox_routes(app, service, mapper)
    _register_meaning_routes(app, service, mapper)
    _register_query_routes(app, service, mapper)
    _register_occurrence_routes(app, service, mapper)
    _register_tag_routes(app, service, mapper)
    _register_relation_routes(app, service, mapper)
    _register_reference_routes(app, service, mapper)
    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Map application exceptions to stable HTTP error responses."""

    @app.exception_handler(ValidationError)
    def validation_error(_request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(exc, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(NotFoundError)
    def not_found_error(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(exc, status.HTTP_404_NOT_FOUND)


def _register_system_routes(app: FastAPI, _service: TermKeeperService) -> None:
    @app.get("/health")
    def health() -> HealthResponse:
        return HealthResponse(status="ok")


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


def _register_meaning_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register meaning lifecycle routes."""

    @app.get("/api/v1/meanings/{meaning_id}")
    def get_meaning(meaning_id: UUID) -> ExternalMeaning:
        return mapper.meaning(service.get_meaning_by_public_id(meaning_id))

    @app.get("/api/v1/meanings")
    def list_meanings(
        tag: str | None = None,
        *,
        favorite_only: bool = False,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> ExternalPage[ExternalMeaning]:
        return page(
            [mapper.meaning(item) for item in service.meanings(tag, favorite_only=favorite_only)],
            offset,
            limit,
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


def _register_query_routes(
    app: FastAPI,
    service: TermKeeperService,
    mapper: ExternalMapper,
) -> None:
    """Register search and analytics routes."""

    @app.get("/api/v1/search")
    def search(
        filters: Annotated[SearchFilters, Query()],
    ) -> ExternalSearchResult:
        query = SearchQuery(
            text=filters.text,
            field=SearchField(filters.field),
            tag=filters.tag,
            favorite_only=filters.favorite_only,
            limit=filters.offset + filters.limit + 1,
        )
        return mapper.search_result(
            service.search(query),
            offset=filters.offset,
            limit=filters.limit,
        )

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> StatsSummary:
        return service.stats(limit)


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
        return page(
            [
                mapper.reference(item)
                for item in service.references(_local_meaning_id(service, meaning_id))
            ],
            offset,
            limit,
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


def _error_response(exc: Exception, status_code: int) -> JSONResponse:
    error = ErrorResponse(error=type(exc).__name__, message=str(exc))
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
    )


def _local_meaning_id(
    service: TermKeeperService,
    public_id: UUID,
    *,
    include_deleted: bool = False,
) -> int:
    return service.get_meaning_by_public_id(
        public_id,
        include_deleted=include_deleted,
    ).meaning_id


def _local_inbox_id(service: TermKeeperService, public_id: UUID) -> int:
    return service.get_inbox_by_public_id(public_id).inbox_id


def main() -> None:
    """Run the local HTTP API."""
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)  # pragma: no cover
