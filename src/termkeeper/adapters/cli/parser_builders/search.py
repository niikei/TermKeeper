"""Shared search command argument builders."""

import argparse

from termkeeper.adapters.cli.parser_builders.common import (
    add_pagination_arguments,
    parse_datetime,
)
from termkeeper.domain import OccurrenceStatus, SearchField


def add_meaning_search_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help="Text to find in terms, names, or descriptions")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--match-all",
        action="store_true",
        dest="match_all",
        default=True,
        help="Require every search word",
    )
    mode.add_argument(
        "--match-any",
        action="store_false",
        dest="match_all",
        help="Accept any search word",
    )
    parser.add_argument(
        "--field",
        choices=tuple(SearchField),
        default=SearchField.ALL,
        dest="search_field",
        type=SearchField,
        help="Field to search",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    parser.add_argument("--tag", help="Filter by tag name")
    parser.add_argument("--scope", help="Filter by registered scope name")
    parser.add_argument(
        "--favorite",
        action="store_true",
        dest="favorite_only",
        help="Show only favorite meanings",
    )
    suggestions = parser.add_mutually_exclusive_group()
    suggestions.add_argument(
        "--suggestions",
        type=int,
        default=3,
        dest="suggestion_limit",
        help="Maximum spelling suggestions",
    )
    suggestions.add_argument(
        "--no-suggestions",
        action="store_const",
        const=0,
        dest="suggestion_limit",
        help="Disable spelling suggestions",
    )


def add_occurrence_search_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help="Text to find in term, memo, or source")
    parser.add_argument("--meaning", type=int, dest="meaning_id", help="Meaning ID")
    parser.add_argument(
        "--status",
        choices=tuple(OccurrenceStatus),
        type=OccurrenceStatus,
        help="Classification status",
    )
    parser.add_argument("--source", help="Exact source filter")
    parser.add_argument("--since", type=parse_datetime, help="ISO 8601 lower time bound")
    add_pagination_arguments(parser, default_limit=20)


def add_inbox_search_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help="Text to find in term, memo, or source")
    parser.add_argument("--source", help="Exact source filter")
    parser.add_argument("--since", type=parse_datetime, help="ISO 8601 lower time bound")
    add_pagination_arguments(parser, default_limit=20)


def add_scope_search_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help="Text to find in scope name or description")
    add_pagination_arguments(parser, default_limit=20)
