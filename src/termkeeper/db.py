import sqlite3
from pathlib import Path

import unicodedata
from datetime import datetime

DB_PATH = Path("data") / "termkeeper.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def normalize_keyword(keyword: str) -> str:
    keyword = unicodedata.normalize("NFKC", keyword)
    return keyword.strip().lower()


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def add_inbox(keyword: str) -> int:
    keyword_norm = normalize_keyword(keyword)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO inbox (
                keyword,
                keyword_norm,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, 'New', ?, ?)
        """,
            (
                keyword,
                keyword_norm,
                now(),
                now(),
            ),
        )

        conn.commit()

        return cur.lastrowid


def list_inbox():
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                inbox_id,
                keyword,
                status,
                created_at
            FROM inbox
            WHERE status IN ('New', 'Pending')
            ORDER BY inbox_id
            """
        )

        return cur.fetchall()


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS inbox (
            inbox_id INTEGER PRIMARY KEY AUTOINCREMENT,

            keyword TEXT NOT NULL,
            keyword_norm TEXT NOT NULL,

            memo TEXT,

            status TEXT NOT NULL DEFAULT 'New',

            resolved_meaning_id INTEGER,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS meaning (
            meaning_id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,
            description TEXT,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS term (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,

            meaning_id INTEGER NOT NULL,

            keyword TEXT NOT NULL,
            keyword_norm TEXT NOT NULL,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            UNIQUE(keyword_norm, meaning_id),

            FOREIGN KEY (meaning_id)
                REFERENCES meaning(meaning_id)
        )
        """)

        conn.commit()


def get_inbox(inbox_id: int):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM inbox
            WHERE inbox_id = ?
            """,
            (inbox_id,),
        )

        return cur.fetchone()


def create_meaning(
    full_name: str,
    description: str,
) -> int:
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO meaning (
                full_name,
                description,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                full_name,
                description,
                now(),
                now(),
            ),
        )

        conn.commit()

        return cur.lastrowid


def add_term(
    meaning_id: int,
    keyword: str,
):
    keyword_norm = normalize_keyword(keyword)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO term (
                meaning_id,
                keyword,
                keyword_norm,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                meaning_id,
                keyword,
                keyword_norm,
                now(),
                now(),
            ),
        )

        conn.commit()


def close_inbox(
    inbox_id: int,
    meaning_id: int,
):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE inbox
            SET
                status = 'Closed',
                resolved_meaning_id = ?,
                updated_at = ?,
                closed_at = ?
            WHERE inbox_id = ?
            """,
            (
                meaning_id,
                now(),
                now(),
                inbox_id,
            ),
        )

        conn.commit()


def search_term(keyword: str):
    keyword_norm = normalize_keyword(keyword)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                m.meaning_id,
                m.full_name,
                m.description
            FROM term t
            JOIN meaning m
                ON t.meaning_id = m.meaning_id
            WHERE t.keyword_norm = ?
            ORDER BY m.meaning_id
            """,
            (keyword_norm,),
        )

        return cur.fetchall()


def find_registered_term(keyword: str):
    keyword_norm = normalize_keyword(keyword)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                m.meaning_id,
                m.full_name,
                m.description
            FROM term t
            JOIN meaning m
                ON t.meaning_id = m.meaning_id
            WHERE t.keyword_norm = ?
            """,
            (keyword_norm,),
        )

        return cur.fetchone()


def find_open_inbox(keyword: str):
    keyword_norm = normalize_keyword(keyword)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                inbox_id,
                keyword,
                status
            FROM inbox
            WHERE keyword_norm = ?
              AND status IN ('New', 'Pending')
            ORDER BY inbox_id
            LIMIT 1
            """,
            (keyword_norm,),
        )

        return cur.fetchone()


def discard_inbox(inbox_id: int):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE inbox
            SET
                status = 'Discarded',
                updated_at = ?,
                closed_at = ?
            WHERE inbox_id = ?
              AND status IN ('New', 'Pending')
            """,
            (
                now(),
                now(),
                inbox_id,
            ),
        )

        conn.commit()

        return cur.rowcount


def list_history():
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                inbox_id,
                keyword,
                status,
                created_at
            FROM inbox
            ORDER BY inbox_id
            """
        )

        return cur.fetchall()


def get_meaning(meaning_id: int):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                meaning_id,
                full_name,
                description
            FROM meaning
            WHERE meaning_id = ?
            """,
            (meaning_id,),
        )

        return cur.fetchone()


def get_terms_by_meaning(meaning_id: int):
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                keyword
            FROM term
            WHERE meaning_id = ?
            ORDER BY keyword
            """,
            (meaning_id,),
        )

        return cur.fetchall()
