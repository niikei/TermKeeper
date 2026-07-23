"""Domain models for TermKeeper."""

from termkeeper.domain.analytics import Frequency, StatsSummary
from termkeeper.domain.importing import ImportIssue, ImportResult, ImportRow
from termkeeper.domain.merge import MergeResult
from termkeeper.domain.models import CaptureResult, Meaning
from termkeeper.domain.occurrence import OccurrenceItem, OccurrenceQuery, OccurrenceUpdate
from termkeeper.domain.pagination import Page
from termkeeper.domain.reference import ReferenceLink, ReferenceUpdate
from termkeeper.domain.scope import GENERAL_SCOPE_PUBLIC_ID, Scope
from termkeeper.domain.search import (
    SearchField,
    SearchHit,
    SearchQuery,
    SearchResult,
    SearchSuggestion,
)
from termkeeper.domain.status import OccurrenceStatus
from termkeeper.domain.tag import TagSummary

__all__ = [
    "CaptureResult",
    "Frequency",
    "GENERAL_SCOPE_PUBLIC_ID",
    "ImportIssue",
    "ImportResult",
    "ImportRow",
    "Meaning",
    "MergeResult",
    "OccurrenceItem",
    "OccurrenceQuery",
    "OccurrenceStatus",
    "OccurrenceUpdate",
    "Page",
    "ReferenceLink",
    "ReferenceUpdate",
    "SearchField",
    "SearchHit",
    "SearchQuery",
    "SearchResult",
    "SearchSuggestion",
    "Scope",
    "StatsSummary",
    "TagSummary",
]
