"""HTTP API adapter backed by TermKeeperService."""

from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import (
    AddResult,
    InboxItem,
    Meaning,
    SearchField,
    SearchQuery,
    SearchResult,
    StatsSummary,
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
    _register_inbox_routes(app, service)
    _register_meaning_routes(app, service)
    _register_query_routes(app, service)
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


def _register_inbox_routes(app: FastAPI, service: TermKeeperService) -> None:
    """Register capture and resolution routes."""

    @app.post("/api/v1/inbox", status_code=status.HTTP_201_CREATED)
    def capture(request: CaptureRequest) -> AddResult:
        return service.add(request.keyword, request.memo, request.source)

    @app.get("/api/v1/inbox")
    def inbox() -> list[InboxItem]:
        return service.inbox()

    @app.post("/api/v1/inbox/{inbox_id}/resolve")
    def resolve(inbox_id: int, request: ResolveRequest) -> Meaning:
        return service.resolve(
            inbox_id,
            request.full_name,
            request.description,
        )


def _register_meaning_routes(app: FastAPI, service: TermKeeperService) -> None:
    """Register meaning lifecycle routes."""

    @app.get("/api/v1/meanings/{meaning_id}")
    def get_meaning(meaning_id: int) -> Meaning:
        return service.get_meaning(meaning_id)

    @app.get("/api/v1/meanings")
    def list_meanings(
        tag: str | None = None,
        *,
        favorite_only: bool = False,
    ) -> list[Meaning]:
        return service.meanings(tag, favorite_only=favorite_only)

    @app.put("/api/v1/meanings/{meaning_id}")
    def update_meaning(
        meaning_id: int,
        request: MeaningUpdateRequest,
    ) -> Meaning:
        return service.edit(
            meaning_id,
            request.full_name,
            request.description,
        )

    @app.delete(
        "/api/v1/meanings/{meaning_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_meaning(meaning_id: int) -> Response:
        service.delete_meaning(meaning_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/v1/trash")
    def list_trash() -> list[Meaning]:
        return service.trash()

    @app.post("/api/v1/trash/{meaning_id}/restore")
    def restore_meaning(meaning_id: int) -> Meaning:
        return service.restore_meaning(meaning_id)


def _register_query_routes(app: FastAPI, service: TermKeeperService) -> None:
    """Register search and analytics routes."""

    @app.get("/api/v1/search")
    def search(
        text: Annotated[str, Query(min_length=1)],
        field: Literal["all", "term", "name", "description"] = "all",
        tag: str | None = None,
        *,
        favorite_only: bool = False,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> SearchResult:
        query = SearchQuery(
            text=text,
            field=SearchField(field),
            tag=tag,
            favorite_only=favorite_only,
            limit=limit,
        )
        return service.search(query)

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> StatsSummary:
        return service.stats(limit)


def _error_response(exc: Exception, status_code: int) -> JSONResponse:
    error = ErrorResponse(error=type(exc).__name__, message=str(exc))
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
    )


def main() -> None:
    """Run the local HTTP API."""
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)  # pragma: no cover
