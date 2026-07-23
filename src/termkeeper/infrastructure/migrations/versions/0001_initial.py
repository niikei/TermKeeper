"""Create the initial TermKeeper schema."""

from alembic import op
from sqlmodel import SQLModel

from termkeeper.infrastructure import tables as _tables  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    SQLModel.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    SQLModel.metadata.drop_all(bind=op.get_bind())
