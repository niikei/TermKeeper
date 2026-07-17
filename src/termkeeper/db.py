from pathlib import Path
import sqlite3

DB_PATH = Path("data") / "termkeeper.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)

    return sqlite3.connect(DB_PATH)


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

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT
        )
        """)

        conn.commit()
