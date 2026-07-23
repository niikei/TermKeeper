"""Search criteria and ranked result DTOs."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from termkeeper.domain.models import Meaning
from termkeeper.domain.query import LogicalOperator


class SearchField(StrEnum):
    TERM = "term"
    NAME = "name"
    DESCRIPTION = "description"


class SearchMode(StrEnum):
    SMART = "smart"
    EXACT = "exact"
    PREFIX = "prefix"
    CONTAINS = "contains"
    GLOB = "glob"
    REGEX = "regex"


@dataclass(frozen=True)
class SearchQuery:
    text: str
    mode: SearchMode = SearchMode.SMART
    fields: tuple[SearchField, ...] = (
        SearchField.TERM,
        SearchField.NAME,
        SearchField.DESCRIPTION,
    )
    word_match: LogicalOperator = LogicalOperator.ALL
    offset: int = 0
    limit: int = 20
    tag: str | None = None
    scope: str | None = None
    favorite_only: bool = False
    suggestion_limit: int = 3


@dataclass(frozen=True)
class SearchHit:
    meaning: Meaning
    score: int
    matched_field: SearchField
    matched_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "meaning": self.meaning.to_dict(),
            "score": self.score,
            "matched_field": self.matched_field,
            "matched_text": self.matched_text,
        }


@dataclass(frozen=True)
class SearchSuggestion:
    meaning: Meaning
    similarity: int
    matched_field: SearchField
    matched_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "meaning": self.meaning.to_dict(),
            "similarity": self.similarity,
            "matched_field": self.matched_field,
            "matched_text": self.matched_text,
        }


@dataclass(frozen=True)
class SearchResult:
    hits: tuple[SearchHit, ...]
    suggestions: tuple[SearchSuggestion, ...] = ()
    offset: int = 0
    limit: int = 20
    has_more: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": [hit.to_dict() for hit in self.hits],
            "suggestions": [suggestion.to_dict() for suggestion in self.suggestions],
            "offset": self.offset,
            "limit": self.limit,
            "has_more": self.has_more,
        }
