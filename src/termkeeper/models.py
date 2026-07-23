"""Domain objects shared by the CLI and future API/MCP adapters."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InboxItem:
    inbox_id: int
    keyword: str
    status: str
    memo: str | None
    source: str | None
    occurrence_count: int
    created_at: str
    updated_at: str
    last_seen_at: str
    closed_at: str | None = None
    resolved_meaning_id: int | None = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "InboxItem":
        return cls(**{name: row[name] for name in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Meaning:
    meaning_id: int
    full_name: str
    description: str | None
    created_at: str
    updated_at: str
    terms: tuple[str, ...] = ()

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
