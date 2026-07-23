"""Small SQLite helpers shared by repositories."""

import unicodedata
from datetime import UTC, datetime


def normalize_keyword(keyword: str) -> str:
    return unicodedata.normalize("NFKC", keyword).strip().casefold()


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
