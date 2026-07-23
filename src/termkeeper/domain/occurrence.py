"""Occurrence history query and result DTOs."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class OccurrenceQuery:
    meaning_id: int | None = None
    inbox_id: int | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    limit: int = 50


@dataclass(frozen=True)
class OccurrenceUpdate:
    keyword: str | None = None
    memo: str | None = None
    source: str | None = None
    clear_memo: bool = False
    clear_source: bool = False


@dataclass(frozen=True)
class OccurrenceItem:
    occurrence_id: int
    keyword: str
    memo: str | None
    source: str | None
    occurred_at: datetime
    updated_at: datetime
    inbox_id: int | None = None
    meaning_id: int | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
