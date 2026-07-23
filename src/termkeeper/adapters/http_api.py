"""HTTP API adapter backed by TermKeeperService."""

from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import SearchField, SearchQuery

type JsonObject = dict[str, object]


class CaptureRequest(BaseModel):
    keyword: str
    memo: str | None = None
    source: str | None = None


class ResolveRequest(BaseModel):
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
    )
    _register_error_handlers(app)
    _register_routes(app, service)
    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Map application exceptions to stable HTTP error responses."""

    @app.exception_handler(ValidationError)
    def validation_error(_request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(exc, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(NotFoundError)
    def not_found_error(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(exc, status.HTTP_404_NOT_FOUND)


def _register_routes(app: FastAPI, service: TermKeeperService) -> None:
    """Register the versioned HTTP surface."""

    @app.get("/health")
    def health() -> JsonObject:
        return {"status": "ok"}

    @app.post("/api/v1/inbox", status_code=status.HTTP_201_CREATED)
    def capture(request: CaptureRequest) -> JsonObject:
        return service.add(request.keyword, request.memo, request.source).to_dict()

    @app.get("/api/v1/inbox")
    def inbox() -> list[JsonObject]:
        return [item.to_dict() for item in service.inbox()]

    @app.post("/api/v1/inbox/{inbox_id}/resolve")
    def resolve(inbox_id: int, request: ResolveRequest) -> JsonObject:
        return service.resolve(
            inbox_id,
            request.full_name,
            request.description,
        ).to_dict()

    @app.get("/api/v1/meanings/{meaning_id}")
    def get_meaning(meaning_id: int) -> JsonObject:
        return service.get_meaning(meaning_id).to_dict()

    @app.get("/api/v1/search")
    def search(
        text: Annotated[str, Query(min_length=1)],
        field: Literal["all", "term", "name", "description"] = "all",
        tag: str | None = None,
        favorite_only: bool = False,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> JsonObject:
        query = SearchQuery(
            text=text,
            field=SearchField(field),
            tag=tag,
            favorite_only=favorite_only,
            limit=limit,
        )
        return service.search(query).to_dict()

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> JsonObject:
        return service.stats(limit).to_dict()


def _error_response(exc: Exception, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "message": str(exc)},
    )


def main() -> None:
    """Run the local HTTP API."""
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)  # pragma: no cover
