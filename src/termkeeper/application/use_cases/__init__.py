"""Feature-oriented application use cases."""

from termkeeper.application.use_cases.config import ConfigUseCases
from termkeeper.application.use_cases.inbox import InboxUseCases
from termkeeper.application.use_cases.meaning import MeaningUseCases
from termkeeper.application.use_cases.occurrence import OccurrenceUseCases

__all__ = ["ConfigUseCases", "InboxUseCases", "MeaningUseCases", "OccurrenceUseCases"]
