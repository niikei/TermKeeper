"""Meaning reference DTOs."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ReferenceLink:
    reference_id: int
    meaning_id: int
    url: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    created_by_id: int | None = None
    updated_by_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReferenceUpdate:
    url: str | None = None
    title: str | None = None
    clear_title: bool = False
