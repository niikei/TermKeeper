"""Occurrence command parsers."""

from termkeeper.adapters.cli.parser_builders.common import (
    Commands,
    add_pagination_arguments,
    parse_datetime,
)
from termkeeper.adapters.cli.parser_builders.search import add_occurrence_search_arguments
from termkeeper.domain import OccurrenceStatus


def add_occurrence_commands(commands: Commands) -> None:
    search = commands.add("search", "Search occurrence history", handler="occurrence-search")
    add_occurrence_search_arguments(search)

    list_ = commands.add("list", "List occurrence history", handler="occurrences")
    list_.add_argument("--meaning", type=int, dest="meaning_id", help="Meaning ID")
    list_.add_argument(
        "--status",
        choices=tuple(OccurrenceStatus),
        type=OccurrenceStatus,
        help="Classification status",
    )
    list_.add_argument("--keyword", help="Filter by encountered term")
    list_.add_argument("--source", help="Filter by source")
    list_.add_argument("--since", type=parse_datetime, help="ISO 8601 lower time bound")
    add_pagination_arguments(list_)

    edit = commands.add("edit", "Edit occurrence context", handler="occurrence-edit")
    edit.add_argument("occurrence_id", type=int, help="Occurrence ID")
    edit.add_argument("--keyword", help="Replacement encountered term")
    memo = edit.add_mutually_exclusive_group()
    memo.add_argument("--memo", help="Replacement memo")
    memo.add_argument("--clear-memo", action="store_true", help="Remove the memo")
    source = edit.add_mutually_exclusive_group()
    source.add_argument("--source", help="Replacement source")
    source.add_argument("--clear-source", action="store_true", help="Remove the source")

    unresolve = commands.add(
        "unresolve",
        "Return a resolved occurrence to inbox",
        handler="unresolve",
    )
    unresolve.add_argument("occurrence_id", type=int, help="Occurrence ID")
    discard = commands.add("discard", "Discard a pending occurrence", handler="discard")
    discard.add_argument("occurrence_id", type=int, help="Occurrence ID")
    reopen = commands.add("reopen", "Return a discarded occurrence to inbox", handler="reopen")
    reopen.add_argument("occurrence_id", type=int, help="Occurrence ID")
