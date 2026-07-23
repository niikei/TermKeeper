"""Argument parser construction for the CLI."""

import argparse
from datetime import datetime

from termkeeper.domain import SearchField


class _Subparsers:
    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self._action = parser.add_subparsers(dest="command", required=True)

    def add(self, name: str, help_text: str) -> argparse.ArgumentParser:
        return self._action.add_parser(name, help=help_text)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tk", description="Capture now, understand later.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    sub = _Subparsers(parser)
    sub.add("init", "Initialize or migrate the database")
    _add_capture_commands(sub)
    _add_meaning_commands(sub)
    _add_config_and_transfer_commands(sub)
    return parser


def _add_capture_commands(sub: _Subparsers) -> None:
    add = sub.add("add", "Add a term to the inbox")
    add.add_argument("keyword")
    add.add_argument("--memo", help="Context or a short reminder")
    add.add_argument("--source", help="Where the term was encountered")
    sub.add("inbox", "Show unresolved items")
    sub.add("history", "Show all captured items")
    inbox_edit = sub.add("inbox-edit", "Edit an open inbox keyword")
    inbox_edit.add_argument("inbox_id", type=int)
    inbox_edit.add_argument("--keyword", required=True)
    occurrences = sub.add("occurrences", "Show occurrence history")
    occurrences.add_argument("--meaning", type=int, dest="meaning_id")
    occurrences.add_argument("--inbox", type=int, dest="inbox_id")
    occurrences.add_argument("--keyword")
    occurrences.add_argument("--source")
    occurrences.add_argument("--since", type=_parse_datetime)
    occurrences.add_argument("--limit", type=int, default=50)
    occurrence_edit = sub.add("occurrence-edit", "Edit occurrence context")
    occurrence_edit.add_argument("occurrence_id", type=int)
    occurrence_edit.add_argument("--keyword")
    occurrence_edit.add_argument("--memo")
    occurrence_edit.add_argument("--source")
    occurrence_edit.add_argument("--clear-memo", action="store_true")
    occurrence_edit.add_argument("--clear-source", action="store_true")
    stats = sub.add("stats", "Show occurrence analytics and rankings")
    stats.add_argument("--limit", type=int, default=10)
    resolve = sub.add("resolve", "Turn an inbox item into a meaning")
    resolve.add_argument("inbox_id", type=int)
    resolve.add_argument("--name", help="Full name (omit for an interactive prompt)")
    resolve.add_argument("--description", help="Description")
    discard = sub.add("discard", "Discard an inbox item")
    discard.add_argument("inbox_id", type=int)


def _add_meaning_commands(sub: _Subparsers) -> None:
    _add_search_command(sub)
    _add_meaning_lifecycle_commands(sub)
    _add_meaning_metadata_commands(sub)


def _add_search_command(sub: _Subparsers) -> None:
    search = sub.add("search", "Search terms and descriptions")
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
    search.add_argument("--favorite", action="store_true", dest="favorite_only")
    suggestions = search.add_mutually_exclusive_group()
    suggestions.add_argument("--suggestions", type=int, default=3, dest="suggestion_limit")
    suggestions.add_argument(
        "--no-suggestions",
        action="store_const",
        const=0,
        dest="suggestion_limit",
    )


def _add_meaning_lifecycle_commands(sub: _Subparsers) -> None:
    show = sub.add("show", "Show a meaning")
    show.add_argument("meaning_id", type=int)
    alias = sub.add("alias", "Add an alias to a meaning")
    alias.add_argument("meaning_id", type=int)
    alias.add_argument("keyword")
    unalias = sub.add("unalias", "Remove an alias from a meaning")
    unalias.add_argument("meaning_id", type=int)
    unalias.add_argument("keyword")
    delete = sub.add("delete", "Move a meaning to trash")
    delete.add_argument("meaning_id", type=int)
    sub.add("trash", "List deleted meanings")
    restore = sub.add("restore", "Restore a deleted meaning")
    restore.add_argument("meaning_id", type=int)
    purge = sub.add("purge", "Permanently delete a trashed meaning")
    purge.add_argument("meaning_id", type=int)
    merge = sub.add("merge", "Merge one meaning into another")
    merge.add_argument("source_id", type=int)
    merge.add_argument("target_id", type=int)
    merge.add_argument("--dry-run", action="store_true")
    edit = sub.add("edit", "Edit a meaning")
    edit.add_argument("meaning_id", type=int)
    edit.add_argument("--name", help="New full name")
    edit.add_argument("--description", help="New description")
    meanings = sub.add("meanings", "List meanings")
    meanings.add_argument("--tag")
    meanings.add_argument("--favorite", action="store_true", dest="favorite_only")


def _add_meaning_metadata_commands(sub: _Subparsers) -> None:
    tag = sub.add("tag", "Add a tag to a meaning")
    tag.add_argument("meaning_id", type=int)
    tag.add_argument("name")
    untag = sub.add("untag", "Remove a tag from a meaning")
    untag.add_argument("meaning_id", type=int)
    untag.add_argument("name")
    sub.add("tags", "List tags")
    favorite = sub.add("favorite", "Mark a meaning as favorite")
    favorite.add_argument("meaning_id", type=int)
    unfavorite = sub.add("unfavorite", "Remove a meaning from favorites")
    unfavorite.add_argument("meaning_id", type=int)
    relate = sub.add("relate", "Relate two meanings")
    relate.add_argument("meaning_id", type=int)
    relate.add_argument("related_id", type=int)
    unrelate = sub.add("unrelate", "Remove a meaning relationship")
    unrelate.add_argument("meaning_id", type=int)
    unrelate.add_argument("related_id", type=int)
    related = sub.add("related", "List related meanings")
    related.add_argument("meaning_id", type=int)
    reference_add = sub.add("reference-add", "Add a reference URL")
    reference_add.add_argument("meaning_id", type=int)
    reference_add.add_argument("url")
    reference_add.add_argument("--title")
    reference_edit = sub.add("reference-edit", "Edit a reference URL")
    reference_edit.add_argument("reference_id", type=int)
    reference_edit.add_argument("--url")
    reference_edit.add_argument("--title")
    reference_edit.add_argument("--clear-title", action="store_true")
    reference_remove = sub.add("reference-remove", "Remove a reference URL")
    reference_remove.add_argument("reference_id", type=int)
    references = sub.add("references", "List reference URLs")
    references.add_argument("meaning_id", type=int)


def _add_config_and_transfer_commands(
    sub: _Subparsers,
) -> None:
    config = sub.add("config", "Get or set user configuration")
    config.add_argument("key", nargs="?", choices=("user.name", "user.email"))
    config.add_argument("value", nargs="?")
    config.add_argument("--list", action="store_true", dest="list_config")
    config.add_argument("--unset", action="store_true")
    export = sub.add("export", "Export meanings to CSV")
    export.add_argument("path", nargs="?", default="termkeeper_export.csv")
    import_ = sub.add("import", "Import meanings from CSV")
    import_.add_argument("path")
    import_.add_argument("--dry-run", action="store_true")
    import_.add_argument("--strict", action="store_true")


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        message = f"invalid ISO 8601 date or datetime: {value}"
        raise argparse.ArgumentTypeError(message) from exc
