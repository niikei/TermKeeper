"""Repository facade retained as a stable application-layer dependency."""

from termkeeper.infrastructure.inbox_repository import (
    add_inbox,
    close_inbox,
    discard_inbox,
    find_open_inbox,
    get_inbox,
    list_history,
    list_inbox,
    touch_inbox,
)
from termkeeper.infrastructure.meaning_repository import (
    add_term,
    create_meaning,
    find_registered_term,
    get_meaning,
    get_terms_by_meaning,
    list_meanings,
    list_meanings_for_export,
    meaning_exists,
    search_term,
    update_meaning,
)
from termkeeper.infrastructure.sqlite_utils import normalize_keyword, now

__all__ = [
    "add_inbox",
    "add_term",
    "close_inbox",
    "create_meaning",
    "discard_inbox",
    "find_open_inbox",
    "find_registered_term",
    "get_inbox",
    "get_meaning",
    "get_terms_by_meaning",
    "list_history",
    "list_inbox",
    "list_meanings",
    "list_meanings_for_export",
    "meaning_exists",
    "normalize_keyword",
    "now",
    "search_term",
    "touch_inbox",
    "update_meaning",
]
