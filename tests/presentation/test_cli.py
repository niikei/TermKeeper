import csv
import json
from pathlib import Path

import pytest

from termkeeper import __version__
from termkeeper.presentation.cli.main import main
from termkeeper.presentation.csv_io import encode_values


def _write_import_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = [
        "public_id",
        "full_name",
        "description",
        "terms",
        "tags",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out == f"tk {__version__}\n"


def test_json_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scope", "add", "Finance", "--json"]) == 0
    capsys.readouterr()
    assert main(["--json", "add", "ICMR", "--memo", "monthly close"]) == 0
    added = json.loads(capsys.readouterr().out)
    occurrence_id = added["occurrence"]["occurrence_id"]

    assert main(["--json", "inbox"]) == 0
    inbox = json.loads(capsys.readouterr().out)
    assert inbox["items"][0]["keyword"] == "ICMR"
    assert inbox["offset"] == 0
    assert inbox["has_more"] is False

    assert (
        main(
            [
                "--json",
                "resolve",
                str(occurrence_id),
                "--name",
                "Intercompany Matching",
                "--scope",
                "Finance",
            ],
        )
        == 0
    )
    meaning = json.loads(capsys.readouterr().out)
    assert meaning["full_name"] == "Intercompany Matching"
    assert meaning["scope"] == "Finance"
    assert "ICMR" in meaning["terms"]

    assert main(["search", "ICMR", "--field", "term", "--limit", "1", "--json"]) == 0
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


def test_initialization_error_hides_internal_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_initialization() -> None:
        message = "database exploded"
        raise RuntimeError(message)

    monkeypatch.setattr("termkeeper.application.service.init_db", fail_initialization)

    assert main(["config"]) == 1
    captured = capsys.readouterr()
    assert "Could not initialize the TermKeeper database" in captured.err
    assert "Traceback" not in captured.err
    assert captured.out == ""


def test_debug_initialization_error_includes_original_traceback(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_initialization() -> None:
        message = "database exploded"
        raise RuntimeError(message)

    monkeypatch.setattr("termkeeper.application.service.init_db", fail_initialization)

    assert main(["--debug", "config"]) == 1
    captured = capsys.readouterr()
    assert "Traceback" in captured.err
    assert "database exploded" in captured.err


def test_human_readable_management_commands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init"]) == 0
    assert main(["add", "ERP", "--source", "meeting"]) == 0
    assert main(["inbox"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["meaning", "alias-add", "1", "enterprise planning"]) == 0
    assert (
        main(
            [
                "meaning",
                "edit",
                "1",
                "--name",
                "Enterprise Resource Planning",
                "--description",
                "suite",
            ],
        )
        == 0
    )
    assert main(["search", "suite"]) == 0
    assert main(["show", "1"]) == 0
    assert main(["meaning", "list"]) == 0
    assert main(["occurrence", "history"]) == 0
    assert main(["meaning", "alias-remove", "1", "enterprise planning"]) == 0
    assert main(["meaning", "delete", "1"]) == 0
    output = capsys.readouterr().out
    assert "Enterprise Resource Planning" in output


def test_scope_management_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scope", "add", "SAP", "--description", "Enterprise", "--json"]) == 0
    created = json.loads(capsys.readouterr().out)
    scope_id = created["scope_id"]

    assert main(["scope", "list", "--json"]) == 0
    assert any(item["name"] == "SAP" for item in json.loads(capsys.readouterr().out))
    assert main(["scope", "edit", str(scope_id), "--name", "SAP S/4HANA"]) == 0
    assert "Updated scope" in capsys.readouterr().out
    assert main(["scope", "delete", str(scope_id), "--yes"]) == 0
    assert "Deleted scope" in capsys.readouterr().out


def test_discard_and_empty_inbox(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "remove-me"]) == 0
    assert main(["occurrence", "discard", "1"]) == 0
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
    assert main(["meaning", "edit", "1"]) == 0
    assert "Updated meaning" in capsys.readouterr().out


def test_json_resolve_never_prompts_or_mixes_human_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--json", "add", "MDM"]) == 0
    capsys.readouterr()

    def fail_input(_prompt: str) -> str:
        raise AssertionError("JSON mode must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)

    assert main(["--json", "resolve", "1"]) == 2
    captured = capsys.readouterr()
    error = json.loads(captured.out)
    assert error == {
        "error": "ValidationError",
        "message": "--name is required with --json when creating a meaning.",
    }
    assert captured.err == ""

    assert main(["--json", "resolve", "1", "--name", "Master Data Management"]) == 0
    captured = capsys.readouterr()
    resolved = json.loads(captured.out)
    assert resolved["full_name"] == "Master Data Management"
    assert captured.err == ""


def test_edit_only_prompts_when_no_values_are_provided(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "ERP"]) == 0
    assert (
        main(
            [
                "resolve",
                "1",
                "--name",
                "Enterprise Resource Planning",
                "--description",
                "Original",
            ],
        )
        == 0
    )
    capsys.readouterr()

    def fail_input(_prompt: str) -> str:
        raise AssertionError("explicit edits must not prompt")

    monkeypatch.setattr("builtins.input", fail_input)

    assert main(["meaning", "edit", "1", "--description", "Updated", "--json"]) == 0
    updated = json.loads(capsys.readouterr().out)
    assert updated["full_name"] == "Enterprise Resource Planning"
    assert updated["description"] == "Updated"

    assert main(["scope", "add", "SAP"]) == 0
    capsys.readouterr()
    assert main(["meaning", "edit", "1", "--scope", "SAP"]) == 0
    capsys.readouterr()
    assert main(["--json", "show", "1"]) == 0
    scoped = json.loads(capsys.readouterr().out)
    assert scoped["scope"] == "SAP"
    assert scoped["description"] == "Updated"

    assert main(["meaning", "edit", "1", "--json"]) == 2
    error = json.loads(capsys.readouterr().out)
    assert error["error"] == "ValidationError"
    assert "required with --json" in error["message"]


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
    assert "Captured occurrence #2" in capsys.readouterr().out

    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["add", "ERP"]) == 0
    output = capsys.readouterr().out
    assert "Possible meanings:" in output
    assert "#1 [General] Enterprise Resource Planning" in output

    assert main(["add", "ERP", "--meaning", "1"]) == 0
    assert "Assigned to meaning #1." in capsys.readouterr().out


def test_occurrence_history_human_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP", "--memo", "meeting", "--source", "Teams"]) == 0
    capsys.readouterr()

    assert main(["occurrence", "list", "--source", "teams", "--keyword", "erp"]) == 0
    output = capsys.readouterr().out
    assert "ERP" in output
    assert "memo: meeting" in output

    assert main(["occurrence", "list", "--status", "Pending", "--limit", "1", "--json"]) == 0
    occurrences = json.loads(capsys.readouterr().out)
    assert occurrences["items"][0]["keyword"] == "ERP"
    assert occurrences["items"][0]["status"] == "Pending"
    assert occurrences["items"][0]["occurred_at"].endswith("+00:00")
    assert occurrences["items"][0]["updated_at"].endswith("+00:00")

    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()
    assert main(["occurrence", "list"]) == 0
    assert "meaning: 1" in capsys.readouterr().out


def test_occurrence_page_shows_how_to_continue(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["add", "FIRST"]) == 0
    assert main(["add", "SECOND"]) == 0
    capsys.readouterr()

    assert main(["inbox", "--limit", "1"]) == 0
    assert "Continue with --offset 1" in capsys.readouterr().out

    assert main(["--json", "inbox", "--offset", "1", "--limit", "1"]) == 0
    page = json.loads(capsys.readouterr().out)
    assert len(page["items"]) == 1
    assert page["offset"] == 1
    assert page["has_more"] is False


def test_occurrence_edit_and_classification_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERPP", "--memo", "typo", "--source", "Meeting"]) == 0
    capsys.readouterr()

    assert main(["occurrence", "edit", "1", "--keyword", "ERP"]) == 0
    assert "Updated occurrence #1." in capsys.readouterr().out
    assert main(["occurrence", "edit", "1", "--clear-memo", "--source", "Teams", "--json"]) == 0
    occurrence = json.loads(capsys.readouterr().out)
    assert occurrence["keyword"] == "ERP"
    assert occurrence["memo"] is None
    assert occurrence["source"] == "Teams"
    assert occurrence["updated_at"]

    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["occurrence", "unresolve", "1"]) == 0
    assert "Returned occurrence #1 to the inbox." in capsys.readouterr().out
    assert main(["occurrence", "discard", "1"]) == 0
    assert main(["occurrence", "reopen", "1"]) == 0
    assert "Reopened occurrence #1." in capsys.readouterr().out
    assert main(["resolve", "1", "--meaning", "1"]) == 0
    assert "Assigned occurrence #1 to meaning #1." in capsys.readouterr().out


def test_empty_occurrence_history(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["occurrence", "list", "--since", "2099-01-01"]) == 0
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

    assert main(["meaning", "merge", "1", "2", "--dry-run"]) == 0
    assert "Would merge meaning #1 into #2" in capsys.readouterr().out
    assert main(["show", "1"]) == 0
    capsys.readouterr()

    assert main(["meaning", "merge", "1", "2", "--yes", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["applied"] is True
    assert result["source_meaning_id"] == 1
    assert result["target_meaning_id"] == 2


def test_tag_commands_and_filters(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["tag", "add", "1", "SAP"]) == 0
    assert "Tagged meaning #1" in capsys.readouterr().out

    assert main(["tag", "list"]) == 0
    assert "SAP (1)" in capsys.readouterr().out
    assert main(["meaning", "list", "--tag", "sap"]) == 0
    assert "Tags: SAP" in capsys.readouterr().out
    assert main(["search", "ERP", "--tag", "SAP"]) == 0
    assert "Enterprise Resource Planning" in capsys.readouterr().out

    assert main(["tag", "list", "--json"]) == 0
    tags = json.loads(capsys.readouterr().out)
    assert tags == [{"meaning_count": 1, "name": "SAP"}]
    assert main(["tag", "remove", "1", "sap"]) == 0
    assert "Removed tag 'sap' from meaning #1." in capsys.readouterr().out


def test_favorite_commands_and_filters(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert main(["meaning", "favorite", "1"]) == 0
    assert "Favorited meaning #1." in capsys.readouterr().out
    assert main(["meaning", "list", "--favorite"]) == 0
    assert "★ Enterprise Resource Planning" in capsys.readouterr().out
    assert main(["search", "ERP", "--favorite"]) == 0
    assert "1 match(es)" in capsys.readouterr().out

    assert main(["meaning", "unfavorite", "1"]) == 0
    assert "Unfavorited meaning #1." in capsys.readouterr().out
    assert main(["meaning", "favorite", "1", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["is_favorite"] is True
    assert main(["meaning", "unfavorite", "1", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["is_favorite"] is False
    assert main(["meaning", "list", "--favorite"]) == 0
    assert capsys.readouterr().out == "No meanings found.\n"


def test_related_meaning_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    assert main(["add", "MRP"]) == 0
    assert main(["resolve", "2", "--name", "Material Requirements Planning"]) == 0
    capsys.readouterr()

    assert main(["meaning", "relate", "1", "2"]) == 0
    assert "Related meaning #1 to #2." in capsys.readouterr().out
    assert main(["meaning", "related", "2"]) == 0
    assert "Enterprise Resource Planning" in capsys.readouterr().out
    assert main(["meaning", "related", "1", "--json"]) == 0
    related = json.loads(capsys.readouterr().out)
    assert related[0]["meaning_id"] == 2
    assert main(["meaning", "unrelate", "2", "1"]) == 0
    assert "Unrelated meaning #2 from #1." in capsys.readouterr().out


def test_reference_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
            "reference",
            "add",
                "1",
                "https://example.com/erp",
                "--title",
                "ERP guide",
            ],
        )
        == 0
    )
    assert "Added reference #1" in capsys.readouterr().out
    assert main(["reference", "add", "1", "https://example.com/erp", "--json"]) == 0
    reference = json.loads(capsys.readouterr().out)
    assert reference["reference_id"] == 1

    assert main(["reference", "list", "1"]) == 0
    output = capsys.readouterr().out
    assert "ERP guide" in output
    assert "https://example.com/erp" in output
    assert main(["reference", "edit", "1", "--clear-title"]) == 0
    assert "Updated reference #1." in capsys.readouterr().out
    assert main(["reference", "remove", "1"]) == 0
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
    assert main(["meaning", "delete", "1"]) == 0
    assert "Moved meaning #1 to trash" in capsys.readouterr().out

    assert main(["meaning", "trash"]) == 0
    assert "Deleted:" in capsys.readouterr().out
    assert main(["meaning", "restore", "1"]) == 0
    assert "Restored meaning #1" in capsys.readouterr().out

    assert main(["meaning", "delete", "1"]) == 0
    capsys.readouterr()
    assert main(["occurrence", "unresolve", "1"]) == 0
    assert main(["meaning", "purge", "1", "--yes"]) == 0
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
    _write_import_csv(
        import_path,
        [
            {
                "public_id": "",
                "full_name": "Master Data Management",
                "description": "governance",
                "terms": encode_values(("MDM",)),
                "tags": encode_values(()),
            },
        ],
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
    _write_import_csv(
        path,
        [
            {
                "public_id": "",
                "full_name": "Valid Meaning",
                "description": "",
                "terms": encode_values(("VALID",)),
                "tags": encode_values(()),
            },
            {
                "public_id": "invalid",
                "full_name": "Invalid Meaning",
                "description": "",
                "terms": encode_values(("INVALID",)),
                "tags": encode_values(()),
            },
        ],
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
        main(["occurrence", "list", "--since", "not-a-date"])

    assert exc_info.value.code == 2
    assert "invalid ISO 8601 date or datetime" in capsys.readouterr().err


def test_runtime_options_work_at_each_command_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--json", "scope", "list"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "General"

    assert main(["scope", "--json", "list"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "General"

    assert main(["scope", "list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["name"] == "General"


def test_resolve_rejects_conflicting_target_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["resolve", "1", "--meaning", "1", "--scope", "SAP"]) == 2
    assert "cannot be used with --meaning" in capsys.readouterr().err

    with pytest.raises(SystemExit) as exc_info:
        main(["resolve", "1", "--meaning", "1", "--name", "Conflicting"])
    assert exc_info.value.code == 2


def test_destructive_commands_require_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["scope", "add", "Temporary"]) == 0
    capsys.readouterr()

    assert main(["scope", "delete", "2", "--json"]) == 2
    error = json.loads(capsys.readouterr().out)
    assert "--yes is required" in error["message"]

    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["scope", "delete", "2"]) == 2
    assert "cancelled" in capsys.readouterr().err.lower()

    assert main(["scope", "delete", "2", "--yes"]) == 0
    assert "Deleted scope #2." in capsys.readouterr().out


def test_descriptions_can_be_cleared_explicitly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["scope", "add", "SAP", "--description", "Platform"]) == 0
    assert main(["add", "ERP"]) == 0
    assert (
        main(
            [
                "resolve",
                "1",
                "--name",
                "Enterprise Resource Planning",
                "--description",
                "Suite",
                "--scope",
                "SAP",
            ],
        )
        == 0
    )
    capsys.readouterr()

    assert main(["scope", "edit", "2", "--clear-description", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["description"] is None
    assert main(["meaning", "edit", "1", "--clear-description", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["description"] is None


def test_empty_human_outputs_are_explicit(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["config"]) == 0
    assert capsys.readouterr().out == "No configuration is set.\n"
    assert main(["meaning", "list"]) == 0
    assert capsys.readouterr().out == "No meanings found.\n"
    assert main(["meaning", "trash"]) == 0
    assert capsys.readouterr().out == "Trash is empty.\n"
    assert main(["tag", "list"]) == 0
    assert capsys.readouterr().out == "No tags found.\n"


def test_help_is_grouped_and_contains_examples(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    root_help = capsys.readouterr().out
    assert "Quick start:" in root_help
    assert "occurrence" in root_help
    assert "scope-add" not in root_help

    with pytest.raises(SystemExit):
        main(["scope", "add", "--help"])
    scope_help = capsys.readouterr().out
    assert "tk scope add SAP" in scope_help


def test_search_human_output_is_compact(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "ERP"]) == 0
    assert main(["resolve", "1", "--name", "Enterprise Resource Planning"]) == 0
    capsys.readouterr()

    assert main(["search", "ERP"]) == 0
    output = capsys.readouterr().out
    assert "[1] Enterprise Resource Planning [General]" in output
    assert "score 100" in output
    assert "Created:" not in output
