"""Feature-oriented SQLModel repositories."""

from termkeeper.infrastructure.repositories import analytics as analytics_repository
from termkeeper.infrastructure.repositories import inbox as inbox_repository
from termkeeper.infrastructure.repositories import meaning as meaning_repository
from termkeeper.infrastructure.repositories import reference as reference_repository
from termkeeper.infrastructure.repositories import relation as relation_repository
from termkeeper.infrastructure.repositories import settings as settings_repository
from termkeeper.infrastructure.repositories import tag as tag_repository

__all__ = [
    "analytics_repository",
    "inbox_repository",
    "meaning_repository",
    "reference_repository",
    "relation_repository",
    "settings_repository",
    "tag_repository",
]
