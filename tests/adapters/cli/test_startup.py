"""CLI startup dependency boundaries."""

import subprocess
import sys
import textwrap

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
