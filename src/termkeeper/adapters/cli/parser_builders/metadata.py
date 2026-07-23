"""Tag, reference, and scope command parsers."""

from termkeeper.adapters.cli.parser_builders.common import (
    Commands,
    add_confirmation_argument,
)
from termkeeper.adapters.cli.parser_builders.search import add_scope_search_arguments


def add_tag_commands(commands: Commands) -> None:
    add = commands.add("add", "Add a tag to a meaning", handler="tag")
    add.add_argument("meaning_id", type=int)
    add.add_argument("name")
    remove = commands.add("remove", "Remove a tag from a meaning", handler="untag")
    remove.add_argument("meaning_id", type=int)
    remove.add_argument("name")
    commands.add("list", "List tags", handler="tags")


def add_reference_commands(commands: Commands) -> None:
    add = commands.add("add", "Add a reference URL", handler="reference-add")
    add.add_argument("meaning_id", type=int)
    add.add_argument("url")
    add.add_argument("--title")
    edit = commands.add("edit", "Edit a reference URL", handler="reference-edit")
    edit.add_argument("reference_id", type=int)
    edit.add_argument("--url")
    title = edit.add_mutually_exclusive_group()
    title.add_argument("--title")
    title.add_argument("--clear-title", action="store_true")
    remove = commands.add("remove", "Remove a reference URL", handler="reference-remove")
    remove.add_argument("reference_id", type=int)
    list_ = commands.add("list", "List reference URLs", handler="references")
    list_.add_argument("meaning_id", type=int)


def add_scope_commands(commands: Commands) -> None:
    search = commands.add("search", "Search meaning scopes", handler="scope-search")
    add_scope_search_arguments(search)

    add = commands.add(
        "add",
        "Create a meaning scope",
        handler="scope-add",
        examples='Example:\n  tk scope add SAP --description "SAP platform"',
    )
    add.add_argument("name", help="Unique scope name")
    add.add_argument("--description", help="Scope description")
    commands.add("list", "List meaning scopes", handler="scopes")
    edit = commands.add("edit", "Edit a meaning scope", handler="scope-edit")
    edit.add_argument("scope_id", type=int, help="Scope ID from 'tk scope list'")
    edit.add_argument("--name", help="New scope name")
    description = edit.add_mutually_exclusive_group()
    description.add_argument("--description", help="New description")
    description.add_argument(
        "--clear-description",
        action="store_true",
        help="Remove the description",
    )
    delete = commands.add("delete", "Delete an unused meaning scope", handler="scope-delete")
    delete.add_argument("scope_id", type=int, help="Scope ID")
    add_confirmation_argument(delete)
