"""Occurrence history query and result DTOs."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from termkeeper.domain.status import OccurrenceStatus


@dataclass(frozen=True)
class OccurrenceQuery:
    meaning_id: int | None = None
    status: OccurrenceStatus | None = None
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
    public_id: UUID
    keyword: str
    memo: str | None
    source: str | None
    status: OccurrenceStatus
    occurred_at: datetime
    updated_at: datetime
    meaning_id: int | None = None
    resolved_at: datetime | None = None
    discarded_at: datetime | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None
    resolved_by_id: int | None = None
    discarded_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
