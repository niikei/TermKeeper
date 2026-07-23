"""FastAPI application construction and process entry point."""

from typing import Literal

import uvicorn
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from termkeeper import __version__
from termkeeper.adapters.external import ExternalMapper
from termkeeper.adapters.http.errors import ErrorResponse, register_error_handlers
from termkeeper.adapters.http.routes.analytics import _register_analytics_routes
from termkeeper.adapters.http.routes.capture import _register_capture_routes
from termkeeper.adapters.http.routes.meaning import _register_meaning_routes
from termkeeper.adapters.http.routes.occurrence import _register_occurrence_routes
from termkeeper.adapters.http.routes.reference import _register_reference_routes
from termkeeper.adapters.http.routes.relation import _register_relation_routes
from termkeeper.adapters.http.routes.scope import _register_scope_routes
from termkeeper.adapters.http.routes.tag import _register_tag_routes
from termkeeper.application import TermKeeperService
from termkeeper.domain import Readiness


class HealthResponse(BaseModel):
    status: Literal["ok"]


def create_app(service: TermKeeperService | None = None) -> FastAPI:
    """Create an API app without import-time database side effects."""
    if service is None:
        service = TermKeeperService()
        service.initialize()

    app = FastAPI(
        title="TermKeeper API",
        version=__version__,
        description="Capture unfamiliar terms and organize searchable meanings.",
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        },
    )
    register_error_handlers(app)
    _register_system_routes(app, service)
    mapper = ExternalMapper(service)
    _register_capture_routes(app, service, mapper)
    _register_meaning_routes(app, service, mapper)
    _register_analytics_routes(app, service)
    _register_occurrence_routes(app, service, mapper)
    _register_tag_routes(app, service, mapper)
    _register_scope_routes(app, service, mapper)
    _register_relation_routes(app, service, mapper)
    _register_reference_routes(app, service, mapper)
    return app


def _register_system_routes(app: FastAPI, service: TermKeeperService) -> None:
    @app.get("/health")
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/ready")
    def ready(response: Response) -> Readiness:
        readiness = service.readiness()
        if readiness.status != "ready":
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return readiness


def main() -> None:
    """Run the local HTTP API."""
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
