"""Argument parser construction for the CLI."""

import argparse
from datetime import datetime
from typing import Protocol

from termkeeper.domain import SearchField


class _Subparsers(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tk", description="Capture now, understand later.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize or migrate the database")
    _add_capture_commands(sub)
    _add_meaning_commands(sub)
    _add_config_and_transfer_commands(sub)
    return parser


def _add_capture_commands(sub: _Subparsers) -> None:
    add = sub.add_parser("add", help="Add a term to the inbox")
    add.add_argument("keyword")
    add.add_argument("--memo", help="Context or a short reminder")
    add.add_argument("--source", help="Where the term was encountered")
    sub.add_parser("inbox", help="Show unresolved items")
    sub.add_parser("history", help="Show all captured items")
    inbox_edit = sub.add_parser("inbox-edit", help="Edit an open inbox keyword")
    inbox_edit.add_argument("inbox_id", type=int)
    inbox_edit.add_argument("--keyword", required=True)
    occurrences = sub.add_parser("occurrences", help="Show occurrence history")
    occurrences.add_argument("--meaning", type=int, dest="meaning_id")
    occurrences.add_argument("--inbox", type=int, dest="inbox_id")
    occurrences.add_argument("--keyword")
    occurrences.add_argument("--source")
    occurrences.add_argument("--since", type=_parse_datetime)
    occurrences.add_argument("--limit", type=int, default=50)
    occurrence_edit = sub.add_parser("occurrence-edit", help="Edit occurrence context")
    occurrence_edit.add_argument("occurrence_id", type=int)
    occurrence_edit.add_argument("--keyword")
    occurrence_edit.add_argument("--memo")
    occurrence_edit.add_argument("--source")
    occurrence_edit.add_argument("--clear-memo", action="store_true")
    occurrence_edit.add_argument("--clear-source", action="store_true")
    stats = sub.add_parser("stats", help="Show occurrence analytics and rankings")
    stats.add_argument("--limit", type=int, default=10)
    resolve = sub.add_parser("resolve", help="Turn an inbox item into a meaning")
    resolve.add_argument("inbox_id", type=int)
    resolve.add_argument("--name", help="Full name (omit for an interactive prompt)")
    resolve.add_argument("--description", help="Description")
    discard = sub.add_parser("discard", help="Discard an inbox item")
    discard.add_argument("inbox_id", type=int)


def _add_meaning_commands(sub: _Subparsers) -> None:
    search = sub.add_parser("search", help="Search terms and descriptions")
    search.add_argument("keyword")
    mode = search.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true", dest="match_all", default=True)
    mode.add_argument("--any", action="store_false", dest="match_all")
    search.add_argument(
        "--in",
        choices=tuple(SearchField),
        default=SearchField.ALL,
        dest="search_field",
        type=SearchField,
    )
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--tag")
    suggestions = search.add_mutually_exclusive_group()
    suggestions.add_argument("--suggestions", type=int, default=3, dest="suggestion_limit")
    suggestions.add_argument(
        "--no-suggestions",
        action="store_const",
        const=0,
        dest="suggestion_limit",
    )
    show = sub.add_parser("show", help="Show a meaning")
    show.add_argument("meaning_id", type=int)
    alias = sub.add_parser("alias", help="Add an alias to a meaning")
    alias.add_argument("meaning_id", type=int)
    alias.add_argument("keyword")
    unalias = sub.add_parser("unalias", help="Remove an alias from a meaning")
    unalias.add_argument("meaning_id", type=int)
    unalias.add_argument("keyword")
    delete = sub.add_parser("delete", help="Move a meaning to trash")
    delete.add_argument("meaning_id", type=int)
    sub.add_parser("trash", help="List deleted meanings")
    restore = sub.add_parser("restore", help="Restore a deleted meaning")
    restore.add_argument("meaning_id", type=int)
    purge = sub.add_parser("purge", help="Permanently delete a trashed meaning")
    purge.add_argument("meaning_id", type=int)
    merge = sub.add_parser("merge", help="Merge one meaning into another")
    merge.add_argument("source_id", type=int)
    merge.add_argument("target_id", type=int)
    merge.add_argument("--dry-run", action="store_true")
    tag = sub.add_parser("tag", help="Add a tag to a meaning")
    tag.add_argument("meaning_id", type=int)
    tag.add_argument("name")
    untag = sub.add_parser("untag", help="Remove a tag from a meaning")
    untag.add_argument("meaning_id", type=int)
    untag.add_argument("name")
    sub.add_parser("tags", help="List tags")

    edit = sub.add_parser("edit", help="Edit a meaning")
    edit.add_argument("meaning_id", type=int)
    edit.add_argument("--name", help="New full name")
    edit.add_argument("--description", help="New description")
    meanings = sub.add_parser("meanings", help="List meanings")
    meanings.add_argument("--tag")


def _add_config_and_transfer_commands(
    sub: _Subparsers,
) -> None:
    config = sub.add_parser("config", help="Get or set user configuration")
    config.add_argument("key", nargs="?", choices=("user.name", "user.email"))
    config.add_argument("value", nargs="?")
    config.add_argument("--list", action="store_true", dest="list_config")
    config.add_argument("--unset", action="store_true")
    export = sub.add_parser("export", help="Export meanings to CSV")
    export.add_argument("path", nargs="?", default="termkeeper_export.csv")
    import_ = sub.add_parser("import", help="Import meanings from CSV")
    import_.add_argument("path")
    import_.add_argument("--dry-run", action="store_true")
    import_.add_argument("--strict", action="store_true")


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        message = f"invalid ISO 8601 date or datetime: {value}"
        raise argparse.ArgumentTypeError(message) from exc
