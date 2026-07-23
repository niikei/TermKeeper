import csv
from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.infrastructure import tag_repository
from termkeeper.presentation.csv_io import export_meanings, import_meanings, split_terms


def test_split_terms_trims_and_ignores_empty_values() -> None:
    assert split_terms(" ERP ; ; Enterprise Resource Planning ") == [
        "ERP",
        "Enterprise Resource Planning",
    ]


def test_csv_round_trip_and_update(tmp_path: Path) -> None:
    service = TermKeeperService()
    captured = service.add("BOM")
    assert captured.inbox is not None
    meaning = service.resolve(captured.inbox.inbox_id, "Bill of Materials", "parts")
    service.add_tag(meaning.meaning_id, "Manufacturing")
    path = tmp_path / "terms.csv"

    assert export_meanings(str(path)) == 1
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    assert rows[0]["public_id"] == str(meaning.public_id)
    assert set(rows[0]["terms"].split(";")) == {"BOM", "Bill of Materials"}
    assert rows[0]["tags"] == "Manufacturing"

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
    assert service.get_meaning(meaning.meaning_id).tags == ("Manufacturing",)


def test_import_creates_meaning_and_aliases(tmp_path: Path) -> None:
    path = tmp_path / "new.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        ",Master Data Management,governance,MDM;master data,Data\n",
        encoding="utf-8",
    )

    result = import_meanings(str(path), TermKeeperService())

    assert (result.created, result.updated, result.skipped) == (1, 0, 0)
    imported = TermKeeperService().search("MDM").hits[0].meaning
    assert imported.description == "governance"
    assert imported.tags == ("Data",)


def test_import_preserves_unknown_public_id(tmp_path: Path) -> None:
    public_id = uuid4()
    path = tmp_path / "external.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        f"{public_id},Customer Relationship Management,customers,CRM,Sales\n",
        encoding="utf-8",
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
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        ",Valid Meaning,,VALID,Test\n"
        "not-a-uuid,Invalid Meaning,,INVALID,\n"
        ",,,,\n",
        encoding="utf-8",
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service, dry_run=True)

    assert result.dry_run is True
    assert (result.created, result.updated, result.skipped) == (1, 0, 2)
    assert [issue.row_number for issue in result.issues] == [3, 4]
    assert service.meanings() == []


def test_import_strict_rejects_all_rows(tmp_path: Path) -> None:
    path = tmp_path / "strict.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n,Valid Meaning,,VALID,\n,,,,\n",
        encoding="utf-8",
    )
    service = TermKeeperService()

    with pytest.raises(ValidationError, match="row 3"):
        import_meanings(str(path), service, strict=True)

    assert service.meanings() == []


def test_import_skips_duplicate_public_id_in_file(tmp_path: Path) -> None:
    public_id = uuid4()
    path = tmp_path / "duplicate.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        f"{public_id},First Meaning,,FIRST,\n"
        f"{public_id},Second Meaning,,SECOND,\n",
        encoding="utf-8",
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert (result.created, result.skipped) == (1, 1)
    assert result.issues[0].row_number == 3
    assert service.get_meaning_by_public_id(public_id).full_name == "First Meaning"


def test_import_reports_deleted_public_id(tmp_path: Path) -> None:
    service = TermKeeperService()
    meaning = service.create_meaning("Archived")
    service.delete_meaning(meaning.meaning_id)
    path = tmp_path / "deleted.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        f"{meaning.public_id},Archived Updated,,ARCHIVED,\n",
        encoding="utf-8",
    )

    result = import_meanings(str(path), service)

    assert (result.created, result.updated, result.skipped) == (0, 0, 1)
    assert "restore it before import" in result.issues[0].message


def test_import_rolls_back_all_rows_on_runtime_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "rollback.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        ",First Meaning,,FIRST,Safe\n"
        ",Second Meaning,,SECOND,Fail\n",
        encoding="utf-8",
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
