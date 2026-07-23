"""CSV import and export using stable Meaning UUIDs."""

import csv
import json
from collections.abc import Mapping
from pathlib import Path

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import ImportIssue, ImportResult, ImportRow

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


def encode_values(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def decode_values(value: str) -> tuple[str, ...]:
    if not value.strip():
        return ()
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        message = "must be a valid JSON array of strings"
        raise ValueError(message) from exc
    if not isinstance(decoded, list):
        message = "must be a JSON array of strings"
        raise ValueError(message)
    values: list[str] = []
    for item in decoded:
        if not isinstance(item, str) or not item.strip():
            message = "must contain only non-empty strings"
            raise ValueError(message)
        values.append(item.strip())
    return tuple(values)


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
                    "terms": encode_values(row.terms),
                    "tags": encode_values(row.tags),
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
    rows, parse_issues = _read_rows(path)
    if strict and parse_issues:
        message = "; ".join(f"row {issue.row_number}: {issue.message}" for issue in parse_issues)
        raise ValidationError(message)
    result = service.import_meanings(tuple(rows), dry_run=dry_run, strict=strict)
    issues = tuple(
        sorted(
            (*parse_issues, *result.issues),
            key=lambda issue: issue.row_number,
        ),
    )
    return ImportResult(
        created=result.created,
        updated=result.updated,
        skipped=result.skipped + len(parse_issues),
        dry_run=result.dry_run,
        issues=issues,
    )


def _read_rows(path: str) -> tuple[list[ImportRow], list[ImportIssue]]:
    rows: list[ImportRow] = []
    issues: list[ImportIssue] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            parsed, issue = _parse_row(row_number, row)
            if issue is not None:
                issues.append(issue)
            elif parsed is not None:
                rows.append(parsed)
    return rows, issues


def _parse_row(
    row_number: int,
    row: Mapping[str, str | None],
) -> tuple[ImportRow | None, ImportIssue | None]:
    values: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for field in ("terms", "tags"):
        try:
            values[field] = decode_values(row.get(field) or "")
        except ValueError as exc:
            errors.append(f"{field} {exc}")
    if errors:
        return None, ImportIssue(row_number, "; ".join(errors))
    return (
        ImportRow(
            row_number=row_number,
            public_id=(row.get("public_id") or "").strip(),
            full_name=(row.get("full_name") or "").strip(),
            scope=(row.get("scope") or "General").strip(),
            description=(row.get("description") or "").strip() or None,
            terms=values["terms"],
            tags=values["tags"],
        ),
        None,
    )
