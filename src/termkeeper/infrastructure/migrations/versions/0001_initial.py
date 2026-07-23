"""Create the original inbox-oriented TermKeeper schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "userprofile",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "meaning",
        sa.Column("meaning_id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("deleted_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("length(trim(full_name)) > 0"),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["userprofile.user_id"]),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["userprofile.user_id"]),
    )
    op.create_index("ix_meaning_public_id", "meaning", ["public_id"], unique=True)
    op.create_index("ix_meaning_deleted_at", "meaning", ["deleted_at"])
    op.create_index("ix_meaning_is_favorite", "meaning", ["is_favorite"])
    op.create_table(
        "inbox",
        sa.Column("inbox_id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("keyword_norm", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("NEW", "CLOSED", "DISCARDED", name="inboxstatus"),
            nullable=False,
        ),
        sa.Column("resolved_meaning_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("length(trim(keyword)) > 0"),
        sa.ForeignKeyConstraint(
            ["resolved_meaning_id"],
            ["meaning.meaning_id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["userprofile.user_id"]),
    )
    op.create_index("ix_inbox_public_id", "inbox", ["public_id"], unique=True)
    op.create_index(
        "uq_inbox_open_keyword",
        "inbox",
        ["keyword_norm"],
        unique=True,
        sqlite_where=sa.text("status = 'NEW'"),
    )
    op.create_table(
        "term",
        sa.Column("term_id", sa.Integer(), primary_key=True),
        sa.Column("meaning_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("keyword_norm", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["meaning_id"], ["meaning.meaning_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
        sa.UniqueConstraint("keyword_norm", "meaning_id"),
    )
    op.create_index("idx_term_keyword", "term", ["keyword_norm"])
    op.create_index("idx_term_meaning", "term", ["meaning_id"])
    op.create_table(
        "tag",
        sa.Column("tag_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_norm", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
    )
    op.create_index("ix_tag_name_norm", "tag", ["name_norm"], unique=True)
    op.create_table(
        "meaningtag",
        sa.Column("meaning_id", sa.Integer(), primary_key=True),
        sa.Column("tag_id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["meaning_id"], ["meaning.meaning_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.tag_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
    )
    op.create_table(
        "meaningrelation",
        sa.Column("meaning_id_low", sa.Integer(), primary_key=True),
        sa.Column("meaning_id_high", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("meaning_id_low < meaning_id_high"),
        sa.ForeignKeyConstraint(
            ["meaning_id_low"],
            ["meaning.meaning_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["meaning_id_high"],
            ["meaning.meaning_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
    )
    op.create_table(
        "meaningreference",
        sa.Column("reference_id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("meaning_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("length(trim(url)) > 0"),
        sa.ForeignKeyConstraint(["meaning_id"], ["meaning.meaning_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["userprofile.user_id"]),
        sa.UniqueConstraint("meaning_id", "url"),
    )
    op.create_index(
        "ix_meaningreference_public_id",
        "meaningreference",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_meaningreference_meaning_id",
        "meaningreference",
        ["meaning_id"],
    )
    op.create_table(
        "occurrence",
        sa.Column("occurrence_id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("keyword_norm", sa.String(), nullable=False),
        sa.Column("inbox_id", sa.Integer(), nullable=True),
        sa.Column("meaning_id", sa.Integer(), nullable=True),
        sa.Column("memo", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["inbox_id"], ["inbox.inbox_id"]),
        sa.ForeignKeyConstraint(["meaning_id"], ["meaning.meaning_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["userprofile.user_id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["userprofile.user_id"]),
    )
    op.create_index("ix_occurrence_public_id", "occurrence", ["public_id"], unique=True)
    op.create_index("ix_occurrence_keyword_norm", "occurrence", ["keyword_norm"])
    op.create_index("ix_occurrence_occurred_at", "occurrence", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("occurrence")
    op.drop_table("meaningreference")
    op.drop_table("meaningrelation")
    op.drop_table("meaningtag")
    op.drop_table("tag")
    op.drop_table("term")
    op.drop_table("inbox")
    op.drop_table("meaning")
    op.drop_table("userprofile")
