import csv
from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.infrastructure.repositories import tag_repository
from termkeeper.presentation.csv_io import (
    decode_values,
    encode_values,
    export_meanings,
    import_meanings,
)

CSV_FIELDS: list[str] = [
    "public_id",
    "full_name",
    "scope",
    "description",
    "terms",
    "tags",
]


def _row(
    full_name: str = "",
    *,
    public_id: str = "",
    scope: str = "",
    description: str = "",
    terms: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
) -> dict[str, str]:
    return {
        "public_id": public_id,
        "full_name": full_name,
        "scope": scope,
        "description": description,
        "terms": encode_values(terms),
        "tags": encode_values(tags),
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_csv_list_encoding_is_unambiguous() -> None:
    values = (" ERP ", "A;B", 'quoted "value"', "日本語,分類")

    assert decode_values(encode_values(values)) == (
        "ERP",
        "A;B",
        'quoted "value"',
        "日本語,分類",
    )
    assert decode_values("") == ()
    for invalid in ("ERP;MRP", '{"value":"ERP"}', '["ERP", ""]', '["ERP", 1]'):
        with pytest.raises(ValueError):
            decode_values(invalid)


def test_csv_round_trip_and_update(tmp_path: Path) -> None:
    service = TermKeeperService()
    captured = service.add("BOM")
    meaning = service.resolve(
        captured.occurrence.occurrence_id,
        "Bill of Materials",
        "parts",
    )
    service.add_alias(meaning.meaning_id, "SAP;Legacy")
    service.add_alias(meaning.meaning_id, 'quoted "alias", value')
    service.add_tag(meaning.meaning_id, "Manufacturing;Core")
    service.add_tag(meaning.meaning_id, "日本語,分類")
    path = tmp_path / "terms.csv"

    assert export_meanings(str(path)) == 1
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    assert rows[0]["public_id"] == str(meaning.public_id)
    assert set(decode_values(rows[0]["terms"])) == {
        "BOM",
        "Bill of Materials",
        "SAP;Legacy",
        'quoted "alias", value',
    }
    assert set(decode_values(rows[0]["tags"])) == {
        "Manufacturing;Core",
        "日本語,分類",
    }

    rows[0]["full_name"] = "Bill of Material"
    rows[0]["description"] = "updated"
    rows.append(dict.fromkeys(rows[0], ""))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    result = import_meanings(str(path), service)
    assert (result.created, result.updated, result.skipped) == (0, 1, 1)
    assert result.issues[0].row_number == 3
    assert service.get_meaning(meaning.meaning_id).description == "updated"
    assert set(service.get_meaning(meaning.meaning_id).tags) == {
        "Manufacturing;Core",
        "日本語,分類",
    }


def test_import_creates_meaning_and_aliases(tmp_path: Path) -> None:
    path = tmp_path / "new.csv"
    _write_csv(
        path,
        [
            _row(
                "Master Data Management",
                description="governance",
                terms=("MDM", "master data"),
                tags=("Data",),
            ),
        ],
    )

    result = import_meanings(str(path), TermKeeperService())

    assert (result.created, result.updated, result.skipped) == (1, 0, 0)
    imported = TermKeeperService().search("MDM").hits[0].meaning
    assert imported.description == "governance"
    assert imported.tags == ("Data",)


def test_import_reports_invalid_json_list_cells(tmp_path: Path) -> None:
    path = tmp_path / "invalid-lists.csv"
    invalid = _row("Invalid Lists")
    invalid["terms"] = "ERP;MRP"
    invalid["tags"] = '["", 1]'
    _write_csv(
        path,
        [
            _row("Valid Meaning", terms=("VALID",)),
            invalid,
        ],
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert (result.created, result.skipped) == (1, 1)
    assert result.issues[0].row_number == 3
    assert "terms must be a valid JSON array" in result.issues[0].message
    assert "tags must contain only non-empty strings" in result.issues[0].message
    with pytest.raises(ValidationError, match="row 3"):
        import_meanings(str(path), TermKeeperService(), strict=True)


def test_import_preserves_unknown_public_id(tmp_path: Path) -> None:
    public_id = uuid4()
    path = tmp_path / "external.csv"
    _write_csv(
        path,
        [
            _row(
                "Customer Relationship Management",
                public_id=str(public_id),
                description="customers",
                terms=("CRM",),
                tags=("Sales",),
            ),
        ],
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert (result.created, result.updated, result.skipped) == (1, 0, 0)
    assert service.get_meaning_by_public_id(public_id).full_name == (
        "Customer Relationship Management"
    )
    assert service.get_meaning_by_public_id(public_id).tags == ("Sales",)


def test_import_dry_run_reports_issues_without_writing(tmp_path: Path) -> None:
    path = tmp_path / "dry-run.csv"
    _write_csv(
        path,
        [
            _row("Valid Meaning", terms=("VALID",), tags=("Test",)),
            _row("Invalid Meaning", public_id="not-a-uuid", terms=("INVALID",)),
            _row(),
        ],
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service, dry_run=True)

    assert result.dry_run is True
    assert (result.created, result.updated, result.skipped) == (1, 0, 2)
    assert [issue.row_number for issue in result.issues] == [3, 4]
    assert service.meanings() == []


def test_import_strict_rejects_all_rows(tmp_path: Path) -> None:
    path = tmp_path / "strict.csv"
    _write_csv(path, [_row("Valid Meaning", terms=("VALID",)), _row()])
    service = TermKeeperService()

    with pytest.raises(ValidationError, match="row 3"):
        import_meanings(str(path), service, strict=True)

    assert service.meanings() == []


def test_import_skips_duplicate_public_id_in_file(tmp_path: Path) -> None:
    public_id = uuid4()
    path = tmp_path / "duplicate.csv"
    _write_csv(
        path,
        [
            _row("First Meaning", public_id=str(public_id), terms=("FIRST",)),
            _row("Second Meaning", public_id=str(public_id), terms=("SECOND",)),
        ],
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert (result.created, result.skipped) == (1, 1)
    assert result.issues[0].row_number == 3
    assert service.get_meaning_by_public_id(public_id).full_name == "First Meaning"


def test_import_skips_duplicate_name_in_same_scope(tmp_path: Path) -> None:
    path = tmp_path / "duplicate-scope.csv"
    _write_csv(
        path,
        [
            _row("Order", scope="SAP", terms=("ORDER",)),
            _row(" order ", scope=" sap ", terms=("ORDER2",)),
        ],
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert (result.created, result.skipped) == (1, 1)
    assert "same scope" in result.issues[0].message


def test_import_reports_deleted_public_id(tmp_path: Path) -> None:
    service = TermKeeperService()
    meaning = service.create_meaning("Archived")
    service.delete_meaning(meaning.meaning_id)
    path = tmp_path / "deleted.csv"
    _write_csv(
        path,
        [
            _row(
                "Archived Updated",
                public_id=str(meaning.public_id),
                terms=("ARCHIVED",),
            ),
        ],
    )

    result = import_meanings(str(path), service)

    assert (result.created, result.updated, result.skipped) == (0, 0, 1)
    assert "restore it before import" in result.issues[0].message


def test_import_strict_rejects_deleted_public_id(tmp_path: Path) -> None:
    service = TermKeeperService()
    meaning = service.create_meaning("Archived")
    service.delete_meaning(meaning.meaning_id)
    path = tmp_path / "deleted-strict.csv"
    _write_csv(
        path,
        [
            _row(
                "Archived Updated",
                public_id=str(meaning.public_id),
                terms=("ARCHIVED",),
            ),
        ],
    )

    with pytest.raises(ValidationError, match="restore it before import"):
        import_meanings(str(path), service, strict=True)

    assert service.trash()[0].full_name == "Archived"


def test_import_rolls_back_all_rows_on_runtime_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rollback.csv"
    _write_csv(
        path,
        [
            _row("First Meaning", terms=("FIRST",), tags=("Safe",)),
            _row("Second Meaning", terms=("SECOND",), tags=("Fail",)),
        ],
    )
    service = TermKeeperService()
    original_add = tag_repository.add

    def fail_on_tag(
        session: Session,
        meaning_id: int,
        name: str,
        user_id: int | None,
    ) -> bool:
        if name == "Fail":
            raise RuntimeError("simulated failure")
        return original_add(session, meaning_id, name, user_id)

    monkeypatch.setattr(
        "termkeeper.application.use_cases.importing.tag_repository.add",
        fail_on_tag,
    )
    with pytest.raises(RuntimeError):
        import_meanings(str(path), service)

    assert service.meanings() == []
