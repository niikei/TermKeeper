"""Tag summary DTO."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TagSummary:
    name: str
    meaning_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
