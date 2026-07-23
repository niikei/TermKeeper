from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateIndex

from termkeeper.infrastructure.tables import Meaning


def test_active_meaning_unique_index_compiles_for_supported_dialects() -> None:
    table = Meaning.metadata.tables["meaning"]
    index = next(item for item in table.indexes if item.name == "uq_meaning_active_scope_name")

    sqlite_ddl = str(CreateIndex(index).compile(dialect=sqlite.dialect()))
    postgres_ddl = str(CreateIndex(index).compile(dialect=postgresql.dialect()))

    assert "WHERE deleted_at IS NULL" in sqlite_ddl
    assert "WHERE deleted_at IS NULL" in postgres_ddl
