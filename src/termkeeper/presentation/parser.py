"""Argument parser construction for the CLI."""

import argparse

from termkeeper.domain import SearchField


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tk", description="Capture now, understand later.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize or migrate the database")

    add = sub.add_parser("add", help="Add a term to the inbox")
    add.add_argument("keyword")
    add.add_argument("--memo", help="Context or a short reminder")
    add.add_argument("--source", help="Where the term was encountered")
    sub.add_parser("inbox", help="Show unresolved items")
    sub.add_parser("history", help="Show all captured items")

    resolve = sub.add_parser("resolve", help="Turn an inbox item into a meaning")
    resolve.add_argument("inbox_id", type=int)
    resolve.add_argument("--name", help="Full name (omit for an interactive prompt)")
    resolve.add_argument("--description", help="Description")

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
    discard = sub.add_parser("discard", help="Discard an inbox item")
    discard.add_argument("inbox_id", type=int)
    show = sub.add_parser("show", help="Show a meaning")
    show.add_argument("meaning_id", type=int)
    alias = sub.add_parser("alias", help="Add an alias to a meaning")
    alias.add_argument("meaning_id", type=int)
    alias.add_argument("keyword")
    unalias = sub.add_parser("unalias", help="Remove an alias from a meaning")
    unalias.add_argument("meaning_id", type=int)
    unalias.add_argument("keyword")
    delete = sub.add_parser("delete", help="Delete a meaning")
    delete.add_argument("meaning_id", type=int)

    edit = sub.add_parser("edit", help="Edit a meaning")
    edit.add_argument("meaning_id", type=int)
    edit.add_argument("--name", help="New full name")
    edit.add_argument("--description", help="New description")
    sub.add_parser("meanings", help="List meanings")
    config = sub.add_parser("config", help="Get or set user configuration")
    config.add_argument("key", nargs="?", choices=("user.name", "user.email"))
    config.add_argument("value", nargs="?")
    config.add_argument("--list", action="store_true", dest="list_config")
    config.add_argument("--unset", action="store_true")
    export = sub.add_parser("export", help="Export meanings to CSV")
    export.add_argument("path", nargs="?", default="termkeeper_export.csv")
    import_ = sub.add_parser("import", help="Import meanings from CSV")
    import_.add_argument("path")
    return parser
