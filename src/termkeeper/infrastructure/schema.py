"""Create the SQLModel schema for a new TermKeeper database."""

from sqlmodel import SQLModel

from termkeeper.infrastructure import tables  # noqa: F401
from termkeeper.infrastructure.connection import get_engine


def init_db() -> None:
    """Create all tables, constraints, and indexes declared by SQLModel."""
    SQLModel.metadata.create_all(get_engine())
