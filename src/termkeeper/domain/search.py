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
