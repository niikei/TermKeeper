"""Search criteria and ranked result DTOs."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from termkeeper.domain.models import Meaning


class SearchField(StrEnum):
    ALL = "all"
    TERM = "term"
    NAME = "name"
    DESCRIPTION = "description"


@dataclass(frozen=True)
class SearchQuery:
    text: str
    match_all: bool = True
    field: SearchField = SearchField.ALL
    limit: int = 20
    tag: str | None = None
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": [hit.to_dict() for hit in self.hits],
            "suggestions": [suggestion.to_dict() for suggestion in self.suggestions],
        }
