"""Add normalized descriptions for Unicode-aware search."""

import unicodedata

import sqlalchemy as sa
from alembic import op

revision = "0002_description_normalization"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "meaning",
        sa.Column(
            "description_norm",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    meaning = sa.table(
        "meaning",
        sa.column("meaning_id", sa.Integer()),
        sa.column("description", sa.String()),
        sa.column("description_norm", sa.String()),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(meaning.c.meaning_id, meaning.c.description),
    ).all()
    for meaning_id, description in rows:
        connection.execute(
            sa.update(meaning)
            .where(meaning.c.meaning_id == meaning_id)
            .values(description_norm=_normalize(description or "")),
        )


def downgrade() -> None:
    op.drop_column("meaning", "description_norm")


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()
