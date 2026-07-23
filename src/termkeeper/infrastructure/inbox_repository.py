"""SQLite persistence operations for inbox records."""

import sqlite3

from termkeeper.infrastructure.connection import get_connection
from termkeeper.infrastructure.sqlite_utils import inserted_id, normalize_keyword, now


def add_inbox(keyword: str, memo: str | None = None, source: str | None = None) -> int:
    stamp = now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inbox
                (keyword, keyword_norm, memo, source, status, occurrence_count,
                 created_at, updated_at, last_seen_at)
            VALUES (?, ?, ?, ?, 'New', 1, ?, ?, ?)
            """,
            (keyword.strip(), normalize_keyword(keyword), memo, source, stamp, stamp, stamp),
        )
        return inserted_id(cursor)


def touch_inbox(inbox_id: int, memo: str | None = None, source: str | None = None) -> None:
    stamp = now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE inbox SET occurrence_count = occurrence_count + 1,
                memo = COALESCE(?, memo), source = COALESCE(?, source),
                updated_at = ?, last_seen_at = ? WHERE inbox_id = ?
            """,
            (memo, source, stamp, stamp, inbox_id),
        )


def list_inbox() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("""
            SELECT * FROM inbox WHERE status IN ('New', 'Pending')
            ORDER BY last_seen_at DESC, inbox_id DESC
        """).fetchall()


def list_history() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM inbox ORDER BY updated_at DESC, inbox_id DESC",
        ).fetchall()


def get_inbox(inbox_id: int) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute("SELECT * FROM inbox WHERE inbox_id = ?", (inbox_id,)).fetchone()


def find_open_inbox(keyword: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM inbox WHERE keyword_norm = ? AND status IN ('New', 'Pending')
            ORDER BY inbox_id LIMIT 1
            """,
            (normalize_keyword(keyword),),
        ).fetchone()


def close_inbox(inbox_id: int, meaning_id: int) -> int:
    stamp = now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE inbox SET status='Closed', resolved_meaning_id=?, updated_at=?, closed_at=?
            WHERE inbox_id=? AND status IN ('New', 'Pending')
            """,
            (meaning_id, stamp, stamp, inbox_id),
        )
        return cursor.rowcount


def discard_inbox(inbox_id: int) -> int:
    stamp = now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE inbox SET status='Discarded', updated_at=?, closed_at=?
            WHERE inbox_id=? AND status IN ('New', 'Pending')
            """,
            (stamp, stamp, inbox_id),
        )
        return cursor.rowcount
