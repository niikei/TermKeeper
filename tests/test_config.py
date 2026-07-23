from pathlib import Path

import pytest

from termkeeper.config import database_path


def test_database_path_uses_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TERMKEEPER_DB", "~/termkeeper-test.db")

    assert database_path() == Path("~/termkeeper-test.db").expanduser()
