"""CLI startup dependency boundaries."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

_HEAVY_MODULES = ("alembic", "fastapi", "mcp", "sqlalchemy", "sqlmodel", "uvicorn")


@pytest.mark.parametrize(
    ("arguments", "expected_code"),
    [
        (["--help"], 0),
        (["--version"], 0),
        (["completion", "zsh"], 0),
    ],
)
def test_database_free_commands_do_not_load_heavy_stacks(
    arguments: list[str],
    expected_code: int | None,
) -> None:
    script = textwrap.dedent(
        f"""
        import contextlib
        import io
        import sys

        from termkeeper.adapters.cli.main import main

        exit_code = None
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                exit_code = main({arguments!r})
            except SystemExit as exc:
                exit_code = exc.code
        assert exit_code == {expected_code!r}
        loaded = [
            name
            for name in {_HEAVY_MODULES!r}
            if name in sys.modules
        ]
        assert not loaded, loaded
        """,
    )

    subprocess.run([sys.executable, "-c", script], check=True)


def test_application_facade_import_does_not_load_database_stack() -> None:
    script = textwrap.dedent(
        """
        import sys

        from termkeeper.application import TermKeeperService

        assert TermKeeperService
        loaded = [
            name
            for name in ("alembic", "sqlalchemy", "sqlmodel")
            if name in sys.modules
        ]
        assert not loaded, loaded
        """,
    )

    subprocess.run([sys.executable, "-c", script], check=True)


def test_current_database_initialization_does_not_load_alembic(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["TERMKEEPER_DATABASE_URL"] = f"sqlite:///{tmp_path / 'startup.db'}"
    initialize = (
        "from termkeeper.application import TermKeeperService; TermKeeperService().initialize()"
    )
    subprocess.run([sys.executable, "-c", initialize], env=environment, check=True)

    verify_fast_path = textwrap.dedent(
        """
        import sys

        from termkeeper.application import TermKeeperService

        TermKeeperService().initialize()
        assert "alembic" not in sys.modules
        """,
    )
    subprocess.run(
        [sys.executable, "-c", verify_fast_path],
        env=environment,
        check=True,
    )
