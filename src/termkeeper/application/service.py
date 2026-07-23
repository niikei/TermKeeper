"""Public application facade for CLI, HTTP, and MCP adapters."""

from termkeeper.application.use_cases import (
    ConfigUseCases,
    ImportUseCases,
    InboxUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    TagUseCases,
)
from termkeeper.infrastructure.schema import init_db


class TermKeeperService(
    InboxUseCases,
    ImportUseCases,
    MeaningUseCases,
    MergeUseCases,
    OccurrenceUseCases,
    TagUseCases,
    ConfigUseCases,
):
    """Stable entry point composed from feature-oriented use cases."""

    def initialize(self) -> None:
        init_db()
