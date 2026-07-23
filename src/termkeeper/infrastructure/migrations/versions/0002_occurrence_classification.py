"""Replace persistent inbox aggregation with explicit occurrence classification."""

import unicodedata

from alembic import op
from sqlalchemy import inspect, text

revision = "0002_occurrence_classification"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)
    if "inbox" not in inspector.get_table_names():
        return

    op.execute("ALTER TABLE meaning ADD COLUMN full_name_norm VARCHAR NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE meaning ADD COLUMN scope VARCHAR NOT NULL DEFAULT 'General'")
    op.execute("ALTER TABLE meaning ADD COLUMN scope_norm VARCHAR NOT NULL DEFAULT 'general'")
    _backfill_meaning_identity()
    op.execute(
        """
        CREATE UNIQUE INDEX uq_meaning_active_scope_name
        ON meaning (scope_norm, full_name_norm)
        WHERE deleted_at IS NULL
        """,
    )
    op.execute(
        """
        CREATE TABLE occurrence_new (
            occurrence_id INTEGER NOT NULL PRIMARY KEY,
            public_id CHAR(32) NOT NULL,
            keyword VARCHAR NOT NULL,
            keyword_norm VARCHAR NOT NULL,
            status VARCHAR(9) NOT NULL,
            meaning_id INTEGER,
            memo VARCHAR,
            source VARCHAR,
            occurred_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            resolved_at DATETIME,
            discarded_at DATETIME,
            created_by_id INTEGER,
            updated_by_id INTEGER,
            resolved_by_id INTEGER,
            discarded_by_id INTEGER,
            CONSTRAINT ck_occurrence_status_meaning CHECK (
                (status = 'PENDING' AND meaning_id IS NULL) OR
                (status = 'RESOLVED' AND meaning_id IS NOT NULL) OR
                (status = 'DISCARDED' AND meaning_id IS NULL)
            ),
            FOREIGN KEY(meaning_id) REFERENCES meaning (meaning_id) ON DELETE RESTRICT,
            FOREIGN KEY(created_by_id) REFERENCES userprofile (user_id),
            FOREIGN KEY(updated_by_id) REFERENCES userprofile (user_id),
            FOREIGN KEY(resolved_by_id) REFERENCES userprofile (user_id),
            FOREIGN KEY(discarded_by_id) REFERENCES userprofile (user_id),
            UNIQUE (public_id)
        )
        """,
    )
    op.execute(
        """
        INSERT INTO occurrence_new (
            occurrence_id,
            public_id,
            keyword,
            keyword_norm,
            status,
            meaning_id,
            memo,
            source,
            occurred_at,
            updated_at,
            resolved_at,
            discarded_at,
            created_by_id,
            updated_by_id,
            resolved_by_id,
            discarded_by_id
        )
        SELECT
            occurrence.occurrence_id,
            occurrence.public_id,
            occurrence.keyword,
            occurrence.keyword_norm,
            CASE
                WHEN occurrence.meaning_id IS NOT NULL
                     AND occurrence.inbox_id IS NOT NULL THEN 'RESOLVED'
                WHEN inbox.status = 'DISCARDED' THEN 'DISCARDED'
                ELSE 'PENDING'
            END,
            CASE
                WHEN occurrence.meaning_id IS NOT NULL
                     AND occurrence.inbox_id IS NOT NULL THEN occurrence.meaning_id
                ELSE NULL
            END,
            occurrence.memo,
            occurrence.source,
            occurrence.occurred_at,
            occurrence.updated_at,
            CASE
                WHEN occurrence.meaning_id IS NOT NULL
                     AND occurrence.inbox_id IS NOT NULL
                THEN coalesce(inbox.closed_at, occurrence.updated_at)
                ELSE NULL
            END,
            CASE
                WHEN inbox.status = 'DISCARDED'
                THEN coalesce(inbox.closed_at, occurrence.updated_at)
                ELSE NULL
            END,
            occurrence.created_by_id,
            occurrence.updated_by_id,
            CASE
                WHEN occurrence.meaning_id IS NOT NULL
                     AND occurrence.inbox_id IS NOT NULL
                THEN inbox.updated_by_id
                ELSE NULL
            END,
            CASE
                WHEN inbox.status = 'DISCARDED' THEN inbox.updated_by_id
                ELSE NULL
            END
        FROM occurrence
        LEFT JOIN inbox ON inbox.inbox_id = occurrence.inbox_id
        """,
    )
    op.execute("DROP TABLE occurrence")
    op.execute("DROP TABLE inbox")
    op.execute("ALTER TABLE occurrence_new RENAME TO occurrence")
    op.execute("CREATE INDEX ix_occurrence_keyword_norm ON occurrence (keyword_norm)")
    op.execute("CREATE INDEX ix_occurrence_status ON occurrence (status)")
    op.execute("CREATE INDEX ix_occurrence_occurred_at ON occurrence (occurred_at)")
    op.execute("CREATE UNIQUE INDEX ix_occurrence_public_id ON occurrence (public_id)")


def downgrade() -> None:
    message = "Occurrence classification migration is intentionally irreversible."
    raise RuntimeError(message)


def _backfill_meaning_identity() -> None:
    connection = op.get_bind()
    rows = connection.execute(
        text(
            "SELECT meaning_id, full_name, deleted_at FROM meaning ORDER BY meaning_id",
        ),
    ).mappings()
    active_keys: set[tuple[str, str]] = set()
    for row in rows:
        meaning_id = int(row["meaning_id"])
        full_name_norm = _normalize(str(row["full_name"]))
        scope = "General"
        scope_norm = "general"
        key = (scope_norm, full_name_norm)
        if row["deleted_at"] is None and key in active_keys:
            scope = f"Legacy #{meaning_id}"
            scope_norm = _normalize(scope)
            key = (scope_norm, full_name_norm)
        if row["deleted_at"] is None:
            active_keys.add(key)
        connection.execute(
            text(
                "UPDATE meaning "
                "SET full_name_norm = :full_name_norm, "
                "scope = :scope, scope_norm = :scope_norm "
                "WHERE meaning_id = :meaning_id",
            ),
            {
                "full_name_norm": full_name_norm,
                "scope": scope,
                "scope_norm": scope_norm,
                "meaning_id": meaning_id,
            },
        )


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()
