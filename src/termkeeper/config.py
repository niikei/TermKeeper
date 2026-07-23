"""Runtime configuration without import-time filesystem side effects."""

import os
from pathlib import Path

from platformdirs import user_data_path


def database_path() -> Path:
    """Return the configured DB path, defaulting to the OS user data directory."""
    configured = os.environ.get("TERMKEEPER_DB")
    if configured is not None:
        return Path(configured).expanduser()
    return user_data_path("TermKeeper", appauthor=False) / "termkeeper.db"
