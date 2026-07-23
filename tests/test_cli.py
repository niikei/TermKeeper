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

    assert main(["import", str(import_path)]) == 0
    assert "Created 1, updated 0, skipped 0." in capsys.readouterr().out
    assert main(["export", str(export_path)]) == 0
    assert f"Exported 1 meaning(s) to {export_path}." in capsys.readouterr().out
    assert export_path.exists()
