"""Primary workflow command parsers."""

from termkeeper.domain import SearchField
from termkeeper.presentation.cli.parser_builders.common import (
    Commands,
    add_pagination_arguments,
)


def add_primary_commands(commands: Commands) -> None:
    add = commands.add(
        "add",
        "Capture a term",
        handler="add",
        examples=(
            "Examples:\n"
            "  tk add ERP\n"
            "  tk add ICMR --memo \"monthly close\" --source Teams\n"
            "  tk add ERP --meaning 12"
        ),
    )
    add.add_argument("keyword", help="Term exactly as encountered")
    add.add_argument("--memo", help="Context or a short reminder")
    add.add_argument("--source", help="Where the term was encountered")
    add.add_argument("--meaning", type=int, dest="meaning_id", help="Explicit meaning ID")
    add.add_argument(
        "--no-prompt",
        action="store_true",
        help="Keep matching occurrences pending without asking",
    )

    inbox = commands.add("inbox", "Show pending occurrences", handler="inbox")
    add_pagination_arguments(inbox)

    resolve = commands.add(
        "resolve",
        "Classify an occurrence",
        handler="resolve",
        examples=(
            "Examples:\n"
            "  tk resolve 3 --meaning 12\n"
            "  tk resolve 3 --name \"Enterprise Resource Planning\" --scope SAP"
        ),
    )
    resolve.add_argument("occurrence_id", type=int, help="Pending occurrence ID")
    target = resolve.add_mutually_exclusive_group()
    target.add_argument("--meaning", type=int, dest="meaning_id", help="Existing meaning ID")
    target.add_argument("--name", help="Full name for a new meaning")
    resolve.add_argument(
        "--scope",
        help="Registered scope name for a new meaning (default: General)",
    )
    resolve.add_argument("--description", help="Description for a new meaning")

    search = commands.add(
        "search",
        "Search meanings",
        handler="search",
        examples=(
            "Examples:\n"
            "  tk search ERP\n"
            "  tk search \"planning system\" --match-any --field description\n"
            "  tk search ERP --scope SAP --tag Core"
        ),
    )
    search.add_argument("keyword", help="One or more search terms")
    mode = search.add_mutually_exclusive_group()
    mode.add_argument(
        "--match-all",
        action="store_true",
        dest="match_all",
        default=True,
        help="Require every search term",
    )
    mode.add_argument(
        "--match-any",
        action="store_false",
        dest="match_all",
        help="Accept any search term",
    )
    search.add_argument(
        "--field",
        choices=tuple(SearchField),
        default=SearchField.ALL,
        dest="search_field",
        type=SearchField,
        help="Field to search",
    )
    search.add_argument("--limit", type=int, default=20, help="Maximum results")
    search.add_argument("--tag", help="Filter by tag name")
    search.add_argument("--scope", help="Filter by registered scope name")
    search.add_argument(
        "--favorite",
        action="store_true",
        dest="favorite_only",
        help="Show only favorite meanings",
    )
    suggestions = search.add_mutually_exclusive_group()
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

    show = commands.add("show", "Show a meaning", handler="show")
    show.add_argument("meaning_id", type=int, help="Meaning ID")
    history = commands.add("history", "Show all captured occurrences", handler="history")
    add_pagination_arguments(history)
    stats = commands.add("stats", "Show occurrence analytics", handler="stats")
    stats.add_argument("--limit", type=int, default=10, help="Ranking size")
