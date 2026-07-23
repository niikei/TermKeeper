import csv
from pathlib import Path
from uuid import uuid4

from termkeeper.application import TermKeeperService
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
    path = tmp_path / "terms.csv"

    assert export_meanings(str(path)) == 1
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    assert rows[0]["public_id"] == str(meaning.public_id)
    assert set(rows[0]["terms"].split(";")) == {"BOM", "Bill of Materials"}

    rows[0]["full_name"] = "Bill of Material"
    rows[0]["description"] = "updated"
    rows.append(dict.fromkeys(rows[0], ""))
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    result = import_meanings(str(path), service)
    assert result == {"created": 0, "updated": 1, "skipped": 1}
    assert service.get_meaning(meaning.meaning_id).description == "updated"


def test_import_creates_meaning_and_aliases(tmp_path: Path) -> None:
    path = tmp_path / "new.csv"
    path.write_text(
        "public_id,full_name,description,terms\n"
        ",Master Data Management,governance,MDM;master data\n",
        encoding="utf-8",
    )

    result = import_meanings(str(path), TermKeeperService())

    assert result == {"created": 1, "updated": 0, "skipped": 0}
    assert TermKeeperService().search("MDM")[0].description == "governance"


def test_import_preserves_unknown_public_id(tmp_path: Path) -> None:
    public_id = uuid4()
    path = tmp_path / "external.csv"
    path.write_text(
        "public_id,full_name,description,terms\n"
        f"{public_id},Customer Relationship Management,customers,CRM\n",
        encoding="utf-8",
    )
    service = TermKeeperService()

    result = import_meanings(str(path), service)

    assert result == {"created": 1, "updated": 0, "skipped": 0}
    assert service.get_meaning_by_public_id(public_id).full_name == (
        "Customer Relationship Management"
    )
