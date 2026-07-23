"""Small SQLite helpers shared by repositories."""

import sqlite3
import unicodedata
from datetime import UTC, datetime


def normalize_keyword(keyword: str) -> str:
    return unicodedata.normalize("NFKC", keyword).strip().casefold()


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def inserted_id(cursor: sqlite3.Cursor) -> int:
    row_id = cursor.lastrowid
    if row_id is None:
        raise RuntimeError("SQLite did not return an ID for the inserted row.")
    return row_id
