"""Domain DTOs returned by application use cases."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from termkeeper.domain.status import InboxStatus


@dataclass(frozen=True)
class InboxItem:
    inbox_id: int
    keyword: str
    status: InboxStatus
    memo: str | None
    source: str | None
    occurrence_count: int
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    closed_at: datetime | None = None
    resolved_meaning_id: int | None = None
    created_by_id: int | None = None
    updated_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Meaning:
    meaning_id: int
    public_id: UUID
    full_name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    terms: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    created_by_id: int | None = None
    updated_by_id: int | None = None
    deleted_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AddResult:
    outcome: str
    inbox: InboxItem | None = None
    meaning: Meaning | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "inbox": self.inbox.to_dict() if self.inbox else None,
            "meaning": self.meaning.to_dict() if self.meaning else None,
        }
