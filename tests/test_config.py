from pathlib import Path

import pytest

from termkeeper.config import database_path


def test_database_path_uses_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TERMKEEPER_DB", "~/termkeeper-test.db")

    assert database_path() == Path("~/termkeeper-test.db").expanduser()


def test_database_path_uses_os_data_directory_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("TERMKEEPER_DB", raising=False)
    monkeypatch.setattr(
        "termkeeper.config.user_data_path",
        lambda *_args, **_kwargs: tmp_path / "TermKeeper",
    )

    assert database_path() == tmp_path / "TermKeeper" / "termkeeper.db"
