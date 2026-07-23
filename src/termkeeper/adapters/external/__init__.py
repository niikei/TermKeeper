"""Shared external response contracts."""

from termkeeper.adapters.external.models import (
    ExternalCaptureResult,
    ExternalMapper,
    ExternalMeaning,
    ExternalOccurrence,
    ExternalPage,
    ExternalReference,
    ExternalScope,
    ExternalSearchResult,
    page,
)
from termkeeper.adapters.external.queries import (
    inbox_search_query,
    meaning_search_query,
    occurrence_search_query,
    scope_search_query,
)

__all__ = [
    "ExternalCaptureResult",
    "ExternalMapper",
    "ExternalMeaning",
    "ExternalOccurrence",
    "ExternalPage",
    "ExternalReference",
    "ExternalSearchResult",
    "ExternalScope",
    "inbox_search_query",
    "meaning_search_query",
    "occurrence_search_query",
    "page",
    "scope_search_query",
]
