"""Database-independent text normalization for persistence and search."""

import unicodedata


def normalize_keyword(keyword: str) -> str:
    return unicodedata.normalize("NFKC", keyword).strip().casefold()
