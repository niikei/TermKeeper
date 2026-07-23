"""CSV import and export using stable Meaning UUIDs."""

import csv
from pathlib import Path

from termkeeper.application import TermKeeperService
from termkeeper.domain import ImportResult, ImportRow

FIELDS = [
    "public_id",
    "full_name",
    "scope",
    "description",
    "terms",
    "tags",
    "created_at",
    "updated_at",
]


def split_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def export_meanings(path: str, service: TermKeeperService | None = None) -> int:
    service = service or TermKeeperService()
    rows = service.meanings()
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "public_id": row.public_id,
                    "full_name": row.full_name,
                    "scope": row.scope,
                    "description": row.description or "",
                    "terms": ";".join(row.terms),
                    "tags": ";".join(row.tags),
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                },
            )
    return len(rows)


def import_meanings(
    path: str,
    service: TermKeeperService,
    *,
    dry_run: bool = False,
    strict: bool = False,
) -> ImportResult:
    rows: list[ImportRow] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            name = (row.get("full_name") or "").strip()
            scope = (row.get("scope") or "General").strip()
            description = (row.get("description") or "").strip() or None
            terms = tuple(split_terms(row.get("terms") or ""))
            tags = tuple(split_terms(row.get("tags") or ""))
            public_id_text = (row.get("public_id") or "").strip()
            rows.append(
                ImportRow(
                    row_number=row_number,
                    public_id=public_id_text,
                    full_name=name,
                    scope=scope,
                    description=description,
                    terms=terms,
                    tags=tags,
                ),
            )
    return service.import_meanings(tuple(rows), dry_run=dry_run, strict=strict)
