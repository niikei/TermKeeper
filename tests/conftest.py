from collections.abc import Iterator
from pathlib import Path

import pytest

from termkeeper import db


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path) -> Iterator[None]:
    db.configure_database(tmp_path / "termkeeper.db")
    db.init_db()
    yield
    db.configure_database(None)
