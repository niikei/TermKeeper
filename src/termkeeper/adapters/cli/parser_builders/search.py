"""Shared search command argument builders."""

import argparse

from termkeeper.adapters.cli.parser_builders.common import (
    add_pagination_arguments,
    parse_datetime,
)
from termkeeper.domain import (
    LogicalOperator,
    MeaningSort,
    OccurrenceStatus,
    SearchField,
    SortOrder,
)


def add_meaning_list_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="Filter by tag; repeat to provide multiple tags",
    )
    parser.add_argument(
        "--tag-match",
        choices=tuple(LogicalOperator),
        default=LogicalOperator.ALL,
        type=LogicalOperator,
        help="Require all or any repeated --tag values",
    )
    parser.add_argument("--scope", help="Filter by registered scope name")
    parser.add_argument(
        "--favorite",
        action="store_true",
        dest="favorite_only",
        help="Show only favorite meanings",
    )
    parser.add_argument("--created-since", type=parse_datetime, help="ISO 8601 lower time bound")
    parser.add_argument("--updated-since", type=parse_datetime, help="ISO 8601 lower time bound")
    description = parser.add_mutually_exclusive_group()
    description.add_argument(
        "--has-description",
        action="store_const",
        const=True,
        dest="has_description",
        help="Show meanings with descriptions",
    )
    description.add_argument(
        "--without-description",
        action="store_const",
        const=False,
        dest="has_description",
        help="Show meanings without descriptions",
    )
    aliases = parser.add_mutually_exclusive_group()
    aliases.add_argument(
        "--has-alias",
        action="store_const",
        const=True,
        dest="has_alias",
        help="Show meanings with non-canonical aliases",
    )
    aliases.add_argument(
        "--without-alias",
        action="store_const",
        const=False,
        dest="has_alias",
        help="Show meanings without non-canonical aliases",
    )
    parser.add_argument(
        "--sort",
        choices=tuple(MeaningSort),
        default=MeaningSort.UPDATED,
        type=MeaningSort,
        help="Field used to order meanings",
    )
    parser.add_argument(
        "--order",
        choices=tuple(SortOrder),
        default=SortOrder.DESC,
        type=SortOrder,
        help="Sort direction",
    )
    add_pagination_arguments(parser)


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
    add_pagination_arguments(parser, default_limit=20)
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
