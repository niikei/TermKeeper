"""Alembic migration environment."""

from alembic import context
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401
from termkeeper.infrastructure.connection import get_engine

target_metadata = SQLModel.metadata


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
