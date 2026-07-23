"""Public application facade for CLI, HTTP, and MCP adapters."""

from termkeeper.application.use_cases import (
    ConfigUseCases,
    InboxUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    TagUseCases,
)
from termkeeper.infrastructure.schema import init_db


class TermKeeperService(
    InboxUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    TagUseCases,
    ConfigUseCases,
):
    """Stable entry point composed from feature-oriented use cases."""

    def initialize(self) -> None:
        init_db()
