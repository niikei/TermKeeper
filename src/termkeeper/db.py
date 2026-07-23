"""SQLite persistence adapter.

Functions return sqlite rows for backwards compatibility. New integrations should
prefer :class:`termkeeper.service.TermKeeperService`.
"""

import sqlite3
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from termkeeper.config import database_path

_db_path_override: Path | None = None


def configure_database(path: Path | None) -> None:
    """Override the database path (primarily useful for tests and embedding)."""
    global _db_path_override
    _db_path_override = Path(path) if path is not None else None


def get_connection() -> sqlite3.Connection:
    path = _db_path_override or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def normalize_keyword(keyword: str) -> str:
    return unicodedata.normalize("NFKC", keyword).strip().casefold()


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _inserted_id(cursor: sqlite3.Cursor) -> int:
    """Return an INSERT row ID while satisfying runtime and static checks."""
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError("SQLite did not return an ID for the inserted row.")
    return row_id


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def init_db() -> None:
    """Create the schema and safely upgrade databases created by v0.1."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meaning (
                meaning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL CHECK(length(trim(full_name)) > 0),
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inbox (
                inbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL CHECK(length(trim(keyword)) > 0),
                keyword_norm TEXT NOT NULL,
                memo TEXT,
                source TEXT,
                status TEXT NOT NULL DEFAULT 'New'
                    CHECK(status IN ('New', 'Pending', 'Closed', 'Discarded')),
                resolved_meaning_id INTEGER REFERENCES meaning(meaning_id),
                occurrence_count INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                closed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS term (
                term_id INTEGER PRIMARY KEY AUTOINCREMENT,
                meaning_id INTEGER NOT NULL REFERENCES meaning(meaning_id) ON DELETE CASCADE,
                keyword TEXT NOT NULL CHECK(length(trim(keyword)) > 0),
                keyword_norm TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(keyword_norm, meaning_id)
            );
        """)
        # Additive migrations for databases produced by the original MVP.
        inbox_columns = _columns(conn, "inbox")
        for name, definition in (
            ("source", "TEXT"),
            ("occurrence_count", "INTEGER NOT NULL DEFAULT 1"),
            ("last_seen_at", "TEXT"),
        ):
            if name not in inbox_columns:
                conn.execute(f"ALTER TABLE inbox ADD COLUMN {name} {definition}")
        conn.execute(
            "UPDATE inbox SET last_seen_at = COALESCE(last_seen_at, updated_at, created_at)",
        )
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_inbox_open_keyword
                ON inbox(keyword_norm, status);
            CREATE INDEX IF NOT EXISTS idx_term_keyword ON term(keyword_norm);
            CREATE INDEX IF NOT EXISTS idx_term_meaning ON term(meaning_id);
        """)


def add_inbox(keyword: str, memo: str | None = None, source: str | None = None) -> int:
    stamp = now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO inbox
                (keyword, keyword_norm, memo, source, status, occurrence_count,
                 created_at, updated_at, last_seen_at)
            VALUES (?, ?, ?, ?, 'New', 1, ?, ?, ?)
        """,
            (keyword.strip(), normalize_keyword(keyword), memo, source, stamp, stamp, stamp),
        )
        return _inserted_id(cur)


def touch_inbox(inbox_id: int, memo: str | None = None, source: str | None = None) -> None:
    stamp = now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE inbox SET occurrence_count = occurrence_count + 1,
                memo = COALESCE(?, memo), source = COALESCE(?, source),
                updated_at = ?, last_seen_at = ? WHERE inbox_id = ?
        """,
            (memo, source, stamp, stamp, inbox_id),
        )


def list_inbox() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM inbox WHERE status IN ('New', 'Pending')
            ORDER BY last_seen_at DESC, inbox_id DESC
        """).fetchall()


def list_history() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM inbox ORDER BY updated_at DESC, inbox_id DESC",
        ).fetchall()


def get_inbox(inbox_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM inbox WHERE inbox_id = ?", (inbox_id,)).fetchone()


def find_open_inbox(keyword: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM inbox WHERE keyword_norm = ? AND status IN ('New', 'Pending')
            ORDER BY inbox_id LIMIT 1
        """,
            (normalize_keyword(keyword),),
        ).fetchone()


def create_meaning(full_name: str, description: str | None) -> int:
    stamp = now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO meaning(full_name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """,
            (full_name.strip(), description or None, stamp, stamp),
        )
        return _inserted_id(cur)


def add_term(meaning_id: int, keyword: str) -> bool:
    if not keyword.strip():
        return False
    stamp = now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO term
                (meaning_id, keyword, keyword_norm, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (meaning_id, keyword.strip(), normalize_keyword(keyword), stamp, stamp),
        )
        return cur.rowcount > 0


def close_inbox(inbox_id: int, meaning_id: int) -> int:
    stamp = now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE inbox SET status='Closed', resolved_meaning_id=?, updated_at=?, closed_at=?
            WHERE inbox_id=? AND status IN ('New', 'Pending')
        """,
            (meaning_id, stamp, stamp, inbox_id),
        )
        return cur.rowcount


def discard_inbox(inbox_id: int) -> int:
    stamp = now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE inbox SET status='Discarded', updated_at=?, closed_at=?
            WHERE inbox_id=? AND status IN ('New', 'Pending')
        """,
            (stamp, stamp, inbox_id),
        )
        return cur.rowcount


def get_meaning(meaning_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM meaning WHERE meaning_id = ?", (meaning_id,)).fetchone()


def get_terms_by_meaning(meaning_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM term WHERE meaning_id = ? ORDER BY keyword_norm
        """,
            (meaning_id,),
        ).fetchall()


def meaning_exists(meaning_id: int) -> bool:
    return get_meaning(meaning_id) is not None


def find_registered_term(keyword: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT m.* FROM term t JOIN meaning m USING(meaning_id)
            WHERE t.keyword_norm = ? ORDER BY m.meaning_id LIMIT 1
        """,
            (normalize_keyword(keyword),),
        ).fetchone()


def search_term(keyword: str) -> list[sqlite3.Row]:
    pattern = f"%{normalize_keyword(keyword)}%"
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT m.*, COUNT(DISTINCT t2.term_id) AS term_count
            FROM meaning m
            LEFT JOIN term t ON m.meaning_id=t.meaning_id
            LEFT JOIN term t2 ON m.meaning_id=t2.meaning_id
            WHERE t.keyword_norm LIKE ?
               OR lower(m.full_name) LIKE ?
               OR lower(COALESCE(m.description, '')) LIKE ?
            GROUP BY m.meaning_id ORDER BY m.full_name
        """,
            (pattern, pattern, pattern),
        ).fetchall()


def update_meaning(meaning_id: int, full_name: str, description: str | None) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            UPDATE meaning SET full_name=?, description=?, updated_at=? WHERE meaning_id=?
        """,
            (full_name.strip(), description or None, now(), meaning_id),
        )
        return cur.rowcount


def list_meanings() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("""
            SELECT m.*, COUNT(t.term_id) AS term_count FROM meaning m
            LEFT JOIN term t USING(meaning_id) GROUP BY m.meaning_id ORDER BY m.updated_at DESC
        """).fetchall()


def list_meanings_for_export() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("""
            SELECT m.*, GROUP_CONCAT(t.keyword, ';') AS terms FROM meaning m
            LEFT JOIN term t USING(meaning_id) GROUP BY m.meaning_id ORDER BY m.meaning_id
        """).fetchall()
