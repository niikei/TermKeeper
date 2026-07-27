"""Feature-oriented application use cases with lazy public exports."""

from importlib import import_module
from typing import TYPE_CHECKING

_EXPORTS = {
    "AnalyticsUseCases": "analytics",
    "CaptureUseCases": "capture",
    "ClassificationUseCases": "classification",
    "ConfigUseCases": "config",
    "ImportUseCases": "importing",
    "MeaningCommandUseCases": "meaning_command",
    "MeaningLifecycleUseCases": "meaning_lifecycle",
    "MeaningQueryUseCases": "meaning_query",
    "MergeUseCases": "merge",
    "OccurrenceUseCases": "occurrence",
    "ReferenceUseCases": "reference",
    "RelationUseCases": "relation",
    "ScopeUseCases": "scope",
    "SearchUseCases": "search",
    "SystemUseCases": "system",
    "TagUseCases": "tag",
}

if TYPE_CHECKING:
    from termkeeper.application.use_cases.analytics import AnalyticsUseCases as AnalyticsUseCases
    from termkeeper.application.use_cases.capture import CaptureUseCases as CaptureUseCases
    from termkeeper.application.use_cases.classification import (
        ClassificationUseCases as ClassificationUseCases,
    )
    from termkeeper.application.use_cases.config import ConfigUseCases as ConfigUseCases
    from termkeeper.application.use_cases.importing import ImportUseCases as ImportUseCases
    from termkeeper.application.use_cases.meaning_command import (
        MeaningCommandUseCases as MeaningCommandUseCases,
    )
    from termkeeper.application.use_cases.meaning_lifecycle import (
        MeaningLifecycleUseCases as MeaningLifecycleUseCases,
    )
    from termkeeper.application.use_cases.meaning_query import (
        MeaningQueryUseCases as MeaningQueryUseCases,
    )
    from termkeeper.application.use_cases.merge import MergeUseCases as MergeUseCases
    from termkeeper.application.use_cases.occurrence import OccurrenceUseCases as OccurrenceUseCases
    from termkeeper.application.use_cases.reference import ReferenceUseCases as ReferenceUseCases
    from termkeeper.application.use_cases.relation import RelationUseCases as RelationUseCases
    from termkeeper.application.use_cases.scope import ScopeUseCases as ScopeUseCases
    from termkeeper.application.use_cases.search import SearchUseCases as SearchUseCases
    from termkeeper.application.use_cases.system import SystemUseCases as SystemUseCases
    from termkeeper.application.use_cases.tag import TagUseCases as TagUseCases

__all__ = (
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
    "SystemUseCases",
    "TagUseCases",
)


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    value = getattr(import_module(f"{__name__}.{module_name}"), name)
    globals()[name] = value
    return value
