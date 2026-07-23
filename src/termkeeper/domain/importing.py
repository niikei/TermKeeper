"""Batch import input and result DTOs."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImportRow:
    row_number: int
    public_id: str
    full_name: str
    description: str | None
    terms: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportIssue:
    row_number: int
    message: str

    def to_dict(self) -> dict[str, str | int]:
        return {"row_number": self.row_number, "message": self.message}


@dataclass(frozen=True)
class ImportResult:
    created: int
    updated: int
    skipped: int
    dry_run: bool
    issues: tuple[ImportIssue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "dry_run": self.dry_run,
            "issues": [issue.to_dict() for issue in self.issues],
        }
