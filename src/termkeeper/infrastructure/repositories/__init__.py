"""Feature-oriented SQLModel repositories with lazy public aliases."""

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

_EXPORTS = {
    "analytics_repository": "analytics",
    "meaning_repository": "meaning",
    "occurrence_repository": "occurrence",
    "reference_repository": "reference",
    "relation_repository": "relation",
    "settings_repository": "settings",
    "scope_repository": "scope",
    "tag_repository": "tag",
}

if TYPE_CHECKING:
    from termkeeper.infrastructure.repositories import analytics as analytics_repository
    from termkeeper.infrastructure.repositories import meaning as meaning_repository
    from termkeeper.infrastructure.repositories import occurrence as occurrence_repository
    from termkeeper.infrastructure.repositories import reference as reference_repository
    from termkeeper.infrastructure.repositories import relation as relation_repository
    from termkeeper.infrastructure.repositories import scope as scope_repository
    from termkeeper.infrastructure.repositories import settings as settings_repository
    from termkeeper.infrastructure.repositories import tag as tag_repository

__all__ = (
    "analytics_repository",
    "meaning_repository",
    "occurrence_repository",
    "reference_repository",
    "relation_repository",
    "scope_repository",
    "settings_repository",
    "tag_repository",
)


def __getattr__(name: str) -> ModuleType:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    value = import_module(f"{__name__}.{module_name}")
    globals()[name] = value
    return value
