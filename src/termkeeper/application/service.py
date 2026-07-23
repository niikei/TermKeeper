"""Public application facade for CLI, HTTP, and MCP adapters."""

from termkeeper.application.use_cases import (
    ConfigUseCases,
    InboxUseCases,
    MeaningUseCases,
    OccurrenceUseCases,
)
from termkeeper.infrastructure.schema import init_db


class TermKeeperService(InboxUseCases, MeaningUseCases, OccurrenceUseCases, ConfigUseCases):
    """Stable entry point composed from feature-oriented use cases."""

    def initialize(self) -> None:
        init_db()
