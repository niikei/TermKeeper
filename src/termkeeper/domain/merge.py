"""Meaning merge result DTO."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MergeResult:
    source_meaning_id: int
    target_meaning_id: int
    terms_moved: int
    occurrences_moved: int
    inboxes_moved: int
    applied: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
