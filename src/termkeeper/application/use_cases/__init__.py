"""Feature-oriented application use cases."""

from termkeeper.application.use_cases.analytics import AnalyticsUseCases
from termkeeper.application.use_cases.capture import CaptureUseCases
from termkeeper.application.use_cases.classification import ClassificationUseCases
from termkeeper.application.use_cases.config import ConfigUseCases
from termkeeper.application.use_cases.importing import ImportUseCases
from termkeeper.application.use_cases.meaning_command import MeaningCommandUseCases
from termkeeper.application.use_cases.meaning_lifecycle import MeaningLifecycleUseCases
from termkeeper.application.use_cases.meaning_query import MeaningQueryUseCases
from termkeeper.application.use_cases.merge import MergeUseCases
from termkeeper.application.use_cases.occurrence import OccurrenceUseCases
from termkeeper.application.use_cases.reference import ReferenceUseCases
from termkeeper.application.use_cases.relation import RelationUseCases
from termkeeper.application.use_cases.scope import ScopeUseCases
from termkeeper.application.use_cases.search import SearchUseCases
from termkeeper.application.use_cases.system import SystemUseCases
from termkeeper.application.use_cases.tag import TagUseCases

__all__ = [
    "AnalyticsUseCases",
    "CaptureUseCases",
    "ClassificationUseCases",
    "ConfigUseCases",
    "ImportUseCases",
    "MeaningCommandUseCases",
    "MeaningLifecycleUseCases",
    "MeaningQueryUseCases",
    "MergeUseCases",
    "OccurrenceUseCases",
    "ReferenceUseCases",
    "RelationUseCases",
    "ScopeUseCases",
    "SearchUseCases",
    "TagUseCases",
    "SystemUseCases",
]
