import json
from pathlib import Path

import pytest

from termkeeper.presentation.cli.main import main


def test_json_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "add", "ICMR", "--memo", "monthly close"]) == 0
    added = json.loads(capsys.readouterr().out)
    inbox_id = added["inbox"]["inbox_id"]

    assert main(["--json", "inbox"]) == 0
    inbox = json.loads(capsys.readouterr().out)
    assert inbox[0]["keyword"] == "ICMR"

    assert main(["--json", "resolve", str(inbox_id), "--name", "Intercompany Matching"]) == 0
    meaning = json.loads(capsys.readouterr().out)
    assert meaning["full_name"] == "Intercompany Matching"
    assert "ICMR" in meaning["terms"]

    assert main(["--json", "search", "ICMR", "--in", "term", "--limit", "1"]) == 0
    matches = json.loads(capsys.readouterr().out)
    assert matches["hits"][0]["meaning"]["meaning_id"] == meaning["meaning_id"]
    assert matches["hits"][0]["matched_field"] == "term"
    assert matches["suggestions"] == []


def test_cli_error_has_nonzero_exit_code(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", "404"]) == 2
    assert "not found" in capsys.readouterr().err.lower()


def test_json_error_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "show", "404"]) == 2
    error = json.loads(capsys.readouterr().out)
    assert error["error"] == "NotFoundError"


def test_human_readable_management_commands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init"]) == 0
    assert main(["add", "ERP", "--source", "meeting"]) == 0
    assert main(["inbox"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["alias", "1", "enterprise planning"]) == 0
    assert (
        main(["edit", "1", "--name", "Enterprise Resource Planning", "--description", "suite"]) == 0
    )
    assert main(["search", "suite"]) == 0
    assert main(["show", "1"]) == 0
    assert main(["meanings"]) == 0
    assert main(["history"]) == 0
    assert main(["unalias", "1", "enterprise planning"]) == 0
    assert main(["delete", "1"]) == 0
    output = capsys.readouterr().out
    assert "Enterprise Resource Planning" in output


def test_discard_and_empty_inbox(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "remove-me"]) == 0
    assert main(["discard", "1"]) == 0
    assert main(["inbox"]) == 0
    assert "Inbox is empty" in capsys.readouterr().out


def test_interactive_resolve_and_edit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "MDM"]) == 0
    answers = iter(["Master Data Management", "governance"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert main(["resolve", "1"]) == 0
    answers = iter(["", "updated description"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert main(["edit", "1"]) == 0
    assert "Updated meaning" in capsys.readouterr().out


def test_config_set_get_list_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["config", "user.name", "Taro Yamada"]) == 0
    assert main(["config", "user.email", "taro@example.com"]) == 0
    assert main(["config", "user.name"]) == 0
    assert "Taro Yamada" in capsys.readouterr().out

    assert main(["config", "--list"]) == 0
    assert "user.email=taro@example.com" in capsys.readouterr().out

    assert main(["--json", "config", "--list"]) == 0
    settings = json.loads(capsys.readouterr().out)
    assert settings == {"user.email": "taro@example.com", "user.name": "Taro Yamada"}
    assert main(["config", "--unset", "user.email"]) == 0


def test_human_output_for_repeated_and_registered_terms(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["add", "erp"]) == 0
    assert "seen count is now 2" in capsys.readouterr().out

    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["add", "ERP"]) == 0
    assert "Already registered as meaning #1" in capsys.readouterr().out


def test_occurrence_history_human_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP", "--memo", "meeting", "--source", "Teams"]) == 0
    capsys.readouterr()

    assert main(["occurrences", "--source", "teams", "--keyword", "erp"]) == 0
    output = capsys.readouterr().out
    assert "ERP" in output
    assert "memo: meeting" in output

    assert main(["--json", "occurrences", "--inbox", "1", "--limit", "1"]) == 0
    occurrences = json.loads(capsys.readouterr().out)
    assert occurrences[0]["keyword"] == "ERP"
    assert occurrences[0]["inbox_id"] == 1

    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()
    assert main(["occurrences"]) == 0
    assert "meaning: 1" in capsys.readouterr().out


def test_inbox_and_occurrence_edit_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERPP", "--memo", "typo", "--source", "Meeting"]) == 0
    capsys.readouterr()

    assert main(["inbox-edit", "1", "--keyword", "ERP"]) == 0
    assert "Updated inbox #1: ERP" in capsys.readouterr().out
    assert main(["occurrence-edit", "1", "--keyword", "ERP"]) == 0
    assert "Updated occurrence #1." in capsys.readouterr().out
    assert main(["--json", "occurrence-edit", "1", "--clear-memo", "--source", "Teams"]) == 0
    occurrence = json.loads(capsys.readouterr().out)
    assert occurrence["keyword"] == "ERP"
    assert occurrence["memo"] is None
    assert occurrence["source"] == "Teams"
    assert occurrence["updated_at"]


def test_empty_occurrence_history(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["occurrences", "--since", "2099-01-01"]) == 0
    assert "No occurrences found." in capsys.readouterr().out


def test_stats_human_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP", "--source", "Teams"]) == 0
    assert main(["add", "erp", "--source", "teams"]) == 0
    capsys.readouterr()

    assert main(["stats", "--limit", "1"]) == 0
    output = capsys.readouterr().out
    assert "Occurrences: 2" in output
    assert "ERP: 2" in output
    assert "Teams: 2" in output

    assert main(["--json", "stats", "--limit", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["total_occurrences"] == 2
    assert result["top_terms"][0]["count"] == 2
    assert result["top_sources"][0]["value"] == "Teams"


def test_merge_dry_run_and_json_apply(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "SRC"]) == 0
    assert main(["resolve", "1", "--name", "Source Meaning"]) == 0
    assert main(["add", "TGT"]) == 0
    assert main(["resolve", "2", "--name", "Target Meaning"]) == 0
    capsys.readouterr()

    assert main(["merge", "1", "2", "--dry-run"]) == 0
    assert "Would merge meaning #1 into #2" in capsys.readouterr().out
    assert main(["show", "1"]) == 0
    capsys.readouterr()

    assert main(["--json", "merge", "1", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["applied"] is True
    assert result["source_meaning_id"] == 1
    assert result["target_meaning_id"] == 2


def test_tag_commands_and_filters(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["tag", "1", "SAP"]) == 0
    assert "Tagged meaning #1" in capsys.readouterr().out

    assert main(["tags"]) == 0
    assert "SAP (1)" in capsys.readouterr().out
    assert main(["meanings", "--tag", "sap"]) == 0
    assert "Tags: SAP" in capsys.readouterr().out
    assert main(["search", "ERP", "--tag", "SAP"]) == 0
    assert "Enterprise Resource Planning" in capsys.readouterr().out

    assert main(["--json", "tags"]) == 0
    tags = json.loads(capsys.readouterr().out)
    assert tags == [{"meaning_count": 1, "name": "SAP"}]
    assert main(["untag", "1", "sap"]) == 0
    assert "Removed tag 'sap' from meaning #1." in capsys.readouterr().out


def test_favorite_commands_and_filters(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert main(["favorite", "1"]) == 0
    assert "Favorited meaning #1." in capsys.readouterr().out
    assert main(["meanings", "--favorite"]) == 0
    assert "★ Enterprise Resource Planning" in capsys.readouterr().out
    assert main(["search", "ERP", "--favorite"]) == 0
    assert "1 match(es)" in capsys.readouterr().out

    assert main(["unfavorite", "1"]) == 0
    assert "Unfavorited meaning #1." in capsys.readouterr().out
    assert main(["--json", "favorite", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["is_favorite"] is True
    assert main(["--json", "unfavorite", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["is_favorite"] is False
    assert main(["meanings", "--favorite"]) == 0
    assert capsys.readouterr().out == ""


def test_related_meaning_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["add", "MRP"]) == 0
    assert main(["resolve", "2", "--name", "Material Requirements Planning"]) == 0
    capsys.readouterr()

    assert main(["relate", "1", "2"]) == 0
    assert "Related meaning #1 to #2." in capsys.readouterr().out
    assert main(["related", "2"]) == 0
    assert "Enterprise Resource Planning" in capsys.readouterr().out
    assert main(["--json", "related", "1"]) == 0
    related = json.loads(capsys.readouterr().out)
    assert related[0]["meaning_id"] == 2
    assert main(["unrelate", "2", "1"]) == 0
    assert "Unrelated meaning #2 from #1." in capsys.readouterr().out


def test_reference_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "reference-add",
                "1",
                "https://example.com/erp",
                "--title",
                "ERP guide",
            ],
        )
        == 0
    )
    assert "Added reference #1" in capsys.readouterr().out
    assert main(["--json", "reference-add", "1", "https://example.com/erp"]) == 0
    reference = json.loads(capsys.readouterr().out)
    assert reference["reference_id"] == 1

    assert main(["references", "1"]) == 0
    output = capsys.readouterr().out
    assert "ERP guide" in output
    assert "https://example.com/erp" in output
    assert main(["reference-edit", "1", "--clear-title"]) == 0
    assert "Updated reference #1." in capsys.readouterr().out
    assert main(["reference-remove", "1"]) == 0
    assert "Removed reference #1." in capsys.readouterr().out


def test_search_suggestions_human_json_and_disabled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert main(["search", "ERPP"]) == 0
    output = capsys.readouterr().out
    assert "0 match(es)" in output
    assert "Did you mean:" in output
    assert "Enterprise Resource Planning" in output

    assert main(["--json", "search", "ERPP", "--suggestions", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["hits"] == []
    assert result["suggestions"][0]["matched_text"] == "ERP"

    assert main(["--json", "search", "ERPP", "--no-suggestions"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["suggestions"] == []


def test_trash_restore_and_purge_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["delete", "1"]) == 0
    assert "Moved meaning #1 to trash" in capsys.readouterr().out

    assert main(["trash"]) == 0
    assert "Deleted:" in capsys.readouterr().out
    assert main(["restore", "1"]) == 0
    assert "Restored meaning #1" in capsys.readouterr().out

    assert main(["delete", "1"]) == 0
    capsys.readouterr()
    assert main(["purge", "1"]) == 0
    assert "Permanently deleted meaning #1." in capsys.readouterr().out


def test_config_unset_requires_key(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["config", "--unset"]) == 2
    assert "requires a key" in capsys.readouterr().err


def test_human_csv_export_and_import(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_path = tmp_path / "terms.csv"
    import_path = tmp_path / "external.csv"
    import_path.write_text(
        "public_id,full_name,description,terms\n,Master Data Management,governance,MDM\n",
        encoding="utf-8",
    )

    assert main(["import", str(import_path), "--dry-run"]) == 0
    assert "Would create 1, updated 0, skipped 0." in capsys.readouterr().out
    assert main(["import", str(import_path)]) == 0
    assert "Created 1, updated 0, skipped 0." in capsys.readouterr().out
    assert main(["export", str(export_path)]) == 0
    assert f"Exported 1 meaning(s) to {export_path}." in capsys.readouterr().out
    assert export_path.exists()


def test_import_json_issues_and_strict_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text(
        "public_id,full_name,description,terms,tags\n"
        ",Valid Meaning,,VALID,\n"
        "invalid,Invalid Meaning,,INVALID,\n",
        encoding="utf-8",
    )

    assert main(["--json", "import", str(path), "--dry-run"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["created"] == 1
    assert result["skipped"] == 1
    assert result["issues"][0]["row_number"] == 3

    assert main(["import", str(path), "--dry-run"]) == 0
    assert "Row 3: public_id must be a valid UUID" in capsys.readouterr().out

    assert main(["import", str(path), "--strict"]) == 2
    assert "row 3" in capsys.readouterr().err


def test_invalid_occurrence_datetime_is_rejected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["occurrences", "--since", "not-a-date"])

    assert exc_info.value.code == 2
    assert "invalid ISO 8601 date or datetime" in capsys.readouterr().err
