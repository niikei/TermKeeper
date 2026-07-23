"""Shared pagination result."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Page[T]:
    items: tuple[T, ...]
    offset: int
    limit: int
    has_more: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
