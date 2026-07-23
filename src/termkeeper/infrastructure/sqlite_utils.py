"""Small SQLite helpers shared by repositories."""

import unicodedata


def normalize_keyword(keyword: str) -> str:
    return unicodedata.normalize("NFKC", keyword).strip().casefold()
