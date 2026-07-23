"""SQLite schema creation and additive migrations."""

import sqlite3

from termkeeper.infrastructure.connection import get_connection


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}


def init_db() -> None:
    """Create the schema and safely upgrade databases created by v0.1."""
    with get_connection() as connection:
        connection.executescript("""
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
        inbox_columns = _columns(connection, "inbox")
        for name, definition in (
            ("source", "TEXT"),
            ("occurrence_count", "INTEGER NOT NULL DEFAULT 1"),
            ("last_seen_at", "TEXT"),
        ):
            if name not in inbox_columns:
                connection.execute(f"ALTER TABLE inbox ADD COLUMN {name} {definition}")
        connection.execute(
            "UPDATE inbox SET last_seen_at = COALESCE(last_seen_at, updated_at, created_at)",
        )
        connection.executescript("""
            CREATE INDEX IF NOT EXISTS idx_inbox_open_keyword
                ON inbox(keyword_norm, status);
            CREATE INDEX IF NOT EXISTS idx_term_keyword ON term(keyword_norm);
            CREATE INDEX IF NOT EXISTS idx_term_meaning ON term(meaning_id);
        """)
