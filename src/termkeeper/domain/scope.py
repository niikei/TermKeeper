"""Meaning scope DTOs."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

GENERAL_SCOPE_PUBLIC_ID = UUID("00000000-0000-0000-0000-000000000001")


@dataclass(frozen=True)
class ScopeSearchQuery:
    text: str
    offset: int = 0
    limit: int = 20


@dataclass(frozen=True)
class Scope:
    scope_id: int
    public_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    created_by_id: int | None = None
    updated_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
