"""Public application facade for CLI, HTTP, and MCP adapters."""

from termkeeper.application.errors import InitializationError
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
from termkeeper.config import database_path
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
        try:
            init_db()
        except Exception as exc:
            path = database_path().resolve()
            message = (
                f"Could not initialize the TermKeeper database at '{path}'. "
                "Run 'tk --debug init' for technical details."
            )
            raise InitializationError(message) from exc
