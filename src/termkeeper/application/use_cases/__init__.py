"""Feature-oriented application use cases."""

from termkeeper.application.use_cases.analytics import AnalyticsUseCases
from termkeeper.application.use_cases.capture import CaptureUseCases
from termkeeper.application.use_cases.config import ConfigUseCases
from termkeeper.application.use_cases.importing import ImportUseCases
from termkeeper.application.use_cases.meaning import MeaningUseCases
from termkeeper.application.use_cases.merge import MergeUseCases
from termkeeper.application.use_cases.occurrence import OccurrenceUseCases
from termkeeper.application.use_cases.reference import ReferenceUseCases
from termkeeper.application.use_cases.relation import RelationUseCases
from termkeeper.application.use_cases.scope import ScopeUseCases
from termkeeper.application.use_cases.tag import TagUseCases

__all__ = [
    "AnalyticsUseCases",
    "CaptureUseCases",
    "ConfigUseCases",
    "ImportUseCases",
    "MeaningUseCases",
    "MergeUseCases",
    "OccurrenceUseCases",
    "ReferenceUseCases",
    "RelationUseCases",
    "ScopeUseCases",
    "TagUseCases",
]
