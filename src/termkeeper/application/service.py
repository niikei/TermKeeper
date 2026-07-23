"""Public application facade for CLI, HTTP, and MCP adapters."""

from termkeeper.application.use_cases import (
    AnalyticsUseCases,
    CaptureUseCases,
    ConfigUseCases,
    ImportUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    ReferenceUseCases,
    RelationUseCases,
    TagUseCases,
)
from termkeeper.infrastructure.schema import init_db


class TermKeeperService(
    AnalyticsUseCases,
    CaptureUseCases,
    ImportUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    ReferenceUseCases,
    RelationUseCases,
    TagUseCases,
    ConfigUseCases,
):
    """Stable entry point composed from feature-oriented use cases."""

    def initialize(self) -> None:
        init_db()
