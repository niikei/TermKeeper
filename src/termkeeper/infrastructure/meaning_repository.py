"""SQLite persistence operations for meanings and their terms."""

import sqlite3

from termkeeper.infrastructure.connection import get_connection
from termkeeper.infrastructure.sqlite_utils import inserted_id, normalize_keyword, now


def create_meaning(full_name: str, description: str | None) -> int:
    stamp = now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO meaning(full_name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (full_name.strip(), description or None, stamp, stamp),
        )
        return inserted_id(cursor)


def add_term(meaning_id: int, keyword: str) -> bool:
    if not keyword.strip():
        return False
    stamp = now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO term
                (meaning_id, keyword, keyword_norm, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (meaning_id, keyword.strip(), normalize_keyword(keyword), stamp, stamp),
        )
        return cursor.rowcount > 0


def get_meaning(meaning_id: int) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM meaning WHERE meaning_id = ?", (meaning_id,)
        ).fetchone()


def get_terms_by_meaning(meaning_id: int) -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM term WHERE meaning_id = ? ORDER BY keyword_norm",
            (meaning_id,),
        ).fetchall()


def meaning_exists(meaning_id: int) -> bool:
    return get_meaning(meaning_id) is not None


def find_registered_term(keyword: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT m.* FROM term t JOIN meaning m USING(meaning_id)
            WHERE t.keyword_norm = ? ORDER BY m.meaning_id LIMIT 1
            """,
            (normalize_keyword(keyword),),
        ).fetchone()


def search_term(keyword: str) -> list[sqlite3.Row]:
    pattern = f"%{normalize_keyword(keyword)}%"
    with get_connection() as connection:
        return connection.execute(
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
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE meaning SET full_name=?, description=?, updated_at=? WHERE meaning_id=?",
            (full_name.strip(), description or None, now(), meaning_id),
        )
        return cursor.rowcount


def list_meanings() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("""
            SELECT m.*, COUNT(t.term_id) AS term_count FROM meaning m
            LEFT JOIN term t USING(meaning_id) GROUP BY m.meaning_id ORDER BY m.updated_at DESC
        """).fetchall()


def list_meanings_for_export() -> list[sqlite3.Row]:
    with get_connection() as connection:
        return connection.execute("""
            SELECT m.*, GROUP_CONCAT(t.keyword, ';') AS terms FROM meaning m
            LEFT JOIN term t USING(meaning_id) GROUP BY m.meaning_id ORDER BY m.meaning_id
        """).fetchall()
