"""Runtime configuration without import-time filesystem side effects."""

import os
from pathlib import Path


def database_path() -> Path:
    """Return the configured DB path, defaulting to the project-local data dir."""
    return Path(os.environ.get("TERMKEEPER_DB", "data/termkeeper.db")).expanduser()
