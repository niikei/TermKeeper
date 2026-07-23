import pytest

from termkeeper.infrastructure.connection import configure_database, get_engine


def test_unsupported_database_backend_is_rejected_before_driver_loading() -> None:
    configure_database("mysql://localhost/termkeeper")

    with pytest.raises(
        ValueError,
        match="Unsupported database backend 'mysql'",
    ):
        get_engine()
