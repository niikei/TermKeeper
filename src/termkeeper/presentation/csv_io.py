"""CSV import and export using stable Meaning UUIDs."""

import csv
from pathlib import Path
from uuid import UUID

from termkeeper.application import NotFoundError, TermKeeperService
from termkeeper.domain import Meaning

FIELDS = ["public_id", "full_name", "description", "terms", "tags", "created_at", "updated_at"]


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
                    "description": row.description or "",
                    "terms": ";".join(row.terms),
                    "tags": ";".join(row.tags),
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat(),
                },
            )
    return len(rows)


def import_meanings(path: str, service: TermKeeperService) -> dict[str, int]:
    created = updated = skipped = 0
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("full_name") or "").strip()
            if not name:
                skipped += 1
                continue
            description = (row.get("description") or "").strip() or None
            terms = tuple(split_terms(row.get("terms") or ""))
            tags = tuple(split_terms(row.get("tags") or ""))
            public_id_text = (row.get("public_id") or "").strip()
            existing = _find_existing(service, public_id_text)
            if existing is None:
                public_id = UUID(public_id_text) if public_id_text else None
                meaning = service.create_meaning(name, description, terms, public_id)
                for tag in tags:
                    service.add_tag(meaning.meaning_id, tag)
                created += 1
            else:
                service.edit(existing.meaning_id, name, description)
                for term in terms:
                    service.add_alias(existing.meaning_id, term)
                for tag in tags:
                    service.add_tag(existing.meaning_id, tag)
                updated += 1
    return {"created": created, "updated": updated, "skipped": skipped}


def _find_existing(service: TermKeeperService, public_id: str) -> Meaning | None:
    if not public_id:
        return None
    try:
        return service.get_meaning_by_public_id(UUID(public_id))
    except NotFoundError:
        return None
