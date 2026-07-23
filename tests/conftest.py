from collections.abc import Iterator
from pathlib import Path

import pytest

from termkeeper.infrastructure.connection import configure_database
from termkeeper.infrastructure.schema import init_db


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path) -> Iterator[None]:
    configure_database(tmp_path / "termkeeper.db")
    init_db()
    yield
    configure_database(None)
