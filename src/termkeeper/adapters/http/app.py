"""FastAPI application construction and process entry point."""

from typing import Literal

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from termkeeper.adapters.external import ExternalMapper
from termkeeper.adapters.http.routes.inbox import _register_inbox_routes
from termkeeper.adapters.http.routes.meaning import _register_meaning_routes
from termkeeper.adapters.http.routes.occurrence import _register_occurrence_routes
from termkeeper.adapters.http.routes.query import _register_query_routes
from termkeeper.adapters.http.routes.reference import _register_reference_routes
from termkeeper.adapters.http.routes.relation import _register_relation_routes
from termkeeper.adapters.http.routes.tag import _register_tag_routes
from termkeeper.application import NotFoundError, TermKeeperService, ValidationError


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ErrorResponse(BaseModel):
    error: str
    message: str


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
    _register_system_routes(app)
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


def _register_system_routes(app: FastAPI) -> None:
    @app.get("/health")
    def health() -> HealthResponse:
        return HealthResponse(status="ok")


def _error_response(exc: Exception, status_code: int) -> JSONResponse:
    error = ErrorResponse(error=type(exc).__name__, message=str(exc))
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
    )


def main() -> None:
    """Run the local HTTP API."""
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
