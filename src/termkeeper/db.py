import sqlite3
from pathlib import Path

import unicodedata
from datetime import datetime

DB_PATH = Path("data") / "termkeeper.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    return sqlite3.connect(DB_PATH)


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

        cur.execute("""
            SELECT
                inbox_id,
                keyword,
                status,
                created_at
            FROM inbox
            ORDER BY inbox_id
        """)

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
