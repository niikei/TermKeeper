import json

import pytest

from termkeeper.presentation.main import main


def test_json_workflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "add", "ICMR", "--memo", "monthly close"]) == 0
    added = json.loads(capsys.readouterr().out)
    inbox_id = added["inbox"]["inbox_id"]

    assert main(["--json", "resolve", str(inbox_id), "--name", "Intercompany Matching"]) == 0
    meaning = json.loads(capsys.readouterr().out)
    assert meaning["full_name"] == "Intercompany Matching"
    assert "ICMR" in meaning["terms"]


def test_cli_error_has_nonzero_exit_code(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["show", "404"]) == 2
    assert "not found" in capsys.readouterr().err.lower()
