"""CSV import and export operations."""

import csv
from pathlib import Path

from termkeeper.application import TermKeeperService
from termkeeper.infrastructure import repository


def split_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def export_meanings(path: str) -> int:
    rows = repository.list_meanings_for_export()
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["meaning_id", "full_name", "description", "terms", "created_at", "updated_at"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] or "" for field in fields})
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
            id_text = (row.get("meaning_id") or "").strip()
            if id_text and repository.meaning_exists(int(id_text)):
                meaning = service.edit(int(id_text), name, description)
                updated += 1
            else:
                meaning_id = repository.create_meaning(name, description)
                repository.add_term(meaning_id, name)
                meaning = service.get_meaning(meaning_id)
                created += 1
            for term in split_terms(row.get("terms") or ""):
                service.add_alias(meaning.meaning_id, term)
    return {"created": created, "updated": updated, "skipped": skipped}
