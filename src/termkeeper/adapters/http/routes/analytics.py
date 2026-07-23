"""Analytics HTTP routes."""

from typing import Annotated

from fastapi import FastAPI, Query

from termkeeper.application import TermKeeperService
from termkeeper.domain import StatsSummary


def _register_analytics_routes(
    app: FastAPI,
    service: TermKeeperService,
) -> None:
    """Register analytics routes."""

    @app.get("/api/v1/stats")
    def stats(limit: Annotated[int, Query(ge=1, le=100)] = 10) -> StatsSummary:
        return service.stats(limit)
