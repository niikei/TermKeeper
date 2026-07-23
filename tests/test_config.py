from pathlib import Path

import pytest

from termkeeper.config import database_path, database_target, database_url


def test_database_url_uses_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configured = "postgresql+psycopg://termkeeper:secret@db.example/termkeeper"
    monkeypatch.setenv("TERMKEEPER_DATABASE_URL", configured)

    assert database_url() == configured
    assert "secret" not in database_target()
    assert "***" in database_target()


def test_database_url_uses_os_data_directory_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("TERMKEEPER_DATABASE_URL", raising=False)
    monkeypatch.setattr(
        "termkeeper.config.user_data_path",
        lambda *_args, **_kwargs: tmp_path / "TermKeeper",
    )

    assert database_path() == tmp_path / "TermKeeper" / "termkeeper.db"
    assert database_url() == f"sqlite:///{tmp_path / 'TermKeeper' / 'termkeeper.db'}"


def test_invalid_database_url_has_a_safe_display(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TERMKEEPER_DATABASE_URL", "not a database URL")

    assert database_target() == "<invalid TERMKEEPER_DATABASE_URL>"
