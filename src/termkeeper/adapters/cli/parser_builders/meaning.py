"""Meaning command parsers."""

from termkeeper.adapters.cli.parser_builders.common import (
    Commands,
    add_confirmation_argument,
)
from termkeeper.adapters.cli.parser_builders.search import (
    add_meaning_list_arguments,
    add_meaning_search_arguments,
)


def add_meaning_commands(commands: Commands) -> None:
    search = commands.add("search", "Search meanings", handler="search")
    add_meaning_search_arguments(search)

    list_ = commands.add("list", "List meanings", handler="meanings")
    add_meaning_list_arguments(list_)

    edit = commands.add("edit", "Edit a meaning", handler="edit")
    edit.add_argument("meaning_id", type=int, help="Meaning ID")
    edit.add_argument("--name", help="New full name")
    edit.add_argument("--scope", help="New registered scope name")
    description = edit.add_mutually_exclusive_group()
    description.add_argument("--description", help="New description")
    description.add_argument(
        "--clear-description",
        action="store_true",
        help="Remove the description",
    )

    alias_add = commands.add("alias-add", "Add an alias", handler="alias")
    alias_add.add_argument("meaning_id", type=int)
    alias_add.add_argument("keyword")
    alias_remove = commands.add("alias-remove", "Remove an alias", handler="unalias")
    alias_remove.add_argument("meaning_id", type=int)
    alias_remove.add_argument("keyword")

    favorite = commands.add("favorite", "Mark a meaning as favorite", handler="favorite")
    favorite.add_argument("meaning_id", type=int)
    unfavorite = commands.add(
        "unfavorite",
        "Remove a meaning from favorites",
        handler="unfavorite",
    )
    unfavorite.add_argument("meaning_id", type=int)

    relate = commands.add("relate", "Relate two meanings", handler="relate")
    relate.add_argument("meaning_id", type=int)
    relate.add_argument("related_id", type=int)
    unrelate = commands.add("unrelate", "Remove a meaning relationship", handler="unrelate")
    unrelate.add_argument("meaning_id", type=int)
    unrelate.add_argument("related_id", type=int)
    related = commands.add("related", "List related meanings", handler="related")
    related.add_argument("meaning_id", type=int)

    delete = commands.add("delete", "Move a meaning to trash", handler="delete")
    delete.add_argument("meaning_id", type=int)
    commands.add("trash", "List deleted meanings", handler="trash")
    restore = commands.add("restore", "Restore a deleted meaning", handler="restore")
    restore.add_argument("meaning_id", type=int)
    purge = commands.add(
        "purge",
        "Permanently delete a trashed meaning",
        handler="purge",
    )
    purge.add_argument("meaning_id", type=int)
    add_confirmation_argument(purge)
    merge = commands.add("merge", "Merge one meaning into another", handler="merge")
    merge.add_argument("source_id", type=int)
    merge.add_argument("target_id", type=int)
    merge.add_argument("--dry-run", action="store_true", help="Preview without changing data")
    add_confirmation_argument(merge)
