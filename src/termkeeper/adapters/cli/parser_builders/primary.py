"""Primary workflow command parsers."""

from termkeeper.adapters.cli.parser_builders.common import (
    Commands,
    add_pagination_arguments,
)
from termkeeper.adapters.cli.parser_builders.search import (
    add_inbox_search_arguments,
    add_meaning_list_arguments,
    add_meaning_search_arguments,
)


def add_primary_commands(commands: Commands) -> None:
    add = commands.add(
        "add",
        "Capture a term",
        handler="add",
        examples=(
            "Examples:\n"
            "  tk add ERP\n"
            '  tk add ICMR --memo "monthly close" --source Teams\n'
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

    add_many = commands.add(
        "add-many",
        "Capture multiple terms safely",
        handler="add-many",
        examples=(
            "Examples:\n"
            "  tk add-many\n"
            "  tk add-many --term ERP --term CRM\n"
            "  tk add-many --file terms.txt\n"
            "  pbpaste | tk add-many --file - --yes"
        ),
    )
    inputs = add_many.add_mutually_exclusive_group()
    inputs.add_argument(
        "--term",
        action="append",
        dest="terms",
        help="Term to capture; repeat the option for each term",
    )
    inputs.add_argument("--file", help="UTF-8 file with one term per line; use - for stdin")
    add_many.add_argument("--memo", help="Context or reminder shared by every term")
    add_many.add_argument("--source", help="Source shared by every term")
    add_many.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive preview confirmation",
    )

    inbox = commands.add("inbox", "Show pending occurrences", handler="inbox")
    add_pagination_arguments(inbox)
    inbox_actions = Commands(
        inbox,
        dest="inbox_action",
        required=False,
        title="Actions",
        metavar="ACTION",
    )
    inbox.epilog = (
        "Without an action, list pending occurrences. "
        "Run 'tk inbox search --help' for search options."
    )
    inbox_search = inbox_actions.add(
        "search",
        "Search pending occurrences",
        handler="inbox-search",
    )
    add_inbox_search_arguments(inbox_search)

    list_ = commands.add("list", "Show active meanings", handler="term-list")
    add_meaning_list_arguments(list_)

    resolve = commands.add(
        "resolve",
        "Classify an occurrence",
        handler="resolve",
        examples=(
            "Examples:\n"
            "  tk resolve 3 --meaning 12\n"
            '  tk resolve 3 --name "Enterprise Resource Planning" --scope SAP'
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
            '  tk search "planning system" --match-any --field description\n'
            "  tk search ERP --scope SAP --tag Core"
        ),
    )
    add_meaning_search_arguments(search)

    show = commands.add("show", "Show a meaning", handler="show")
    show.add_argument("meaning_id", type=int, help="Meaning ID")
    history = commands.add("history", "Show all captured occurrences", handler="history")
    add_pagination_arguments(history)
    stats = commands.add("stats", "Show occurrence analytics", handler="stats")
    stats.add_argument("--limit", type=int, default=10, help="Ranking size")
