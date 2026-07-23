"""Domain DTOs returned by application use cases."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from termkeeper.domain.occurrence import OccurrenceItem
from termkeeper.domain.query import LogicalOperator, MeaningSort, SortOrder


@dataclass(frozen=True)
class MeaningListQuery:
    tags: tuple[str, ...] = ()
    tag_match: LogicalOperator = LogicalOperator.ALL
    scope: str | None = None
    favorite_only: bool = False
    created_since: datetime | None = None
    updated_since: datetime | None = None
    has_description: bool | None = None
    has_alias: bool | None = None
    sort: MeaningSort = MeaningSort.UPDATED
    order: SortOrder = SortOrder.DESC
    offset: int = 0
    limit: int = 50


@dataclass(frozen=True)
class Meaning:
    meaning_id: int
    public_id: UUID
    full_name: str
    scope_id: int
    scope_public_id: UUID
    scope: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    is_favorite: bool = False
    terms: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    created_by_id: int | None = None
    updated_by_id: int | None = None
    deleted_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaptureResult:
    occurrence: OccurrenceItem
    candidates: tuple[Meaning, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "occurrence": self.occurrence.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True)
class CaptureInput:
    keyword: str
    memo: str | None = None
    source: str | None = None
    meaning_id: int | None = None


@dataclass(frozen=True)
class CaptureBatchResult:
    items: tuple[CaptureResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}
