"""Occurrence analytics DTOs."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Frequency:
    value: str
    count: int
    last_seen_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StatsSummary:
    total_occurrences: int
    pending_occurrences: int
    active_meanings: int
    top_terms: tuple[Frequency, ...]
    top_sources: tuple[Frequency, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_occurrences": self.total_occurrences,
            "pending_occurrences": self.pending_occurrences,
            "active_meanings": self.active_meanings,
            "top_terms": [item.to_dict() for item in self.top_terms],
            "top_sources": [item.to_dict() for item in self.top_sources],
        }
