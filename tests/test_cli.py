import json
from pathlib import Path

import pytest

from termkeeper.presentation.main import main


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
    assert matches[0]["meaning"]["meaning_id"] == meaning["meaning_id"]
    assert matches[0]["matched_field"] == "term"


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


def test_empty_occurrence_history(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["occurrences", "--since", "2099-01-01"]) == 0
    assert "No occurrences found." in capsys.readouterr().out


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

    assert main(["--json", "untag", "1", "sap"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["tags"] == []


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

    assert main(["import", str(path), "--strict"]) == 2
    assert "row 3" in capsys.readouterr().err
