"""Meaning lifecycle and search command handlers."""

import argparse

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import Meaning, MergeResult, SearchQuery, SearchResult
from termkeeper.presentation.cli.handlers.common import confirm_destructive
from termkeeper.presentation.cli.rendering import (
    print_meaning,
    print_search_hit,
    print_search_suggestion,
)


def handle_search(args: argparse.Namespace, service: TermKeeperService) -> SearchResult:
    query = SearchQuery(
        text=args.keyword,
        match_all=args.match_all,
        field=args.search_field,
        limit=args.limit,
        tag=args.tag,
        scope=args.scope,
        favorite_only=args.favorite_only,
        suggestion_limit=args.suggestion_limit,
    )
    result = service.search(query)
    if not args.json:
        print(f"{len(result.hits)} match(es)")
        for item in result.hits:
            print_search_hit(item)
        if result.suggestions:
            print("Did you mean:")
            for suggestion in result.suggestions:
                print_search_suggestion(suggestion)
    return result


def handle_show(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.get_meaning(args.meaning_id)
    if not args.json:
        print_meaning(result)
    return result


def handle_alias(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_alias(args.meaning_id, args.keyword)
    if not args.json:
        print(f"Added alias '{args.keyword}' to meaning #{args.meaning_id}.")
    return result


def handle_unalias(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.remove_alias(args.meaning_id, args.keyword)
    if not args.json:
        print(f"Removed alias '{args.keyword}' from meaning #{args.meaning_id}.")
    return result


def handle_delete(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.delete_meaning(args.meaning_id)
    if not args.json:
        print(f"Moved meaning #{args.meaning_id} to trash.")
    return {"deleted": args.meaning_id}


def handle_trash(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.trash()
    if not args.json:
        if result:
            for item in result:
                print_meaning(item)
        else:
            print("Trash is empty.")
    return result


def handle_restore(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.restore_meaning(args.meaning_id)
    if not args.json:
        print(f"Restored meaning #{args.meaning_id}.")
    return result


def handle_purge(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    confirm_destructive(
        args,
        f"Permanently delete trashed meaning #{args.meaning_id}?",
    )
    service.purge_meaning(args.meaning_id)
    if not args.json:
        print(f"Permanently deleted meaning #{args.meaning_id}.")
    return {"purged": args.meaning_id}


def handle_merge(args: argparse.Namespace, service: TermKeeperService) -> MergeResult:
    if not args.dry_run:
        confirm_destructive(
            args,
            f"Merge meaning #{args.source_id} into #{args.target_id}?",
        )
    result = service.merge_meanings(args.source_id, args.target_id, dry_run=args.dry_run)
    if not args.json:
        action = "Would merge" if args.dry_run else "Merged"
        print(
            f"{action} meaning #{args.source_id} into #{args.target_id}: "
            f"{result.terms_moved} term(s), {result.tags_moved} tag(s), "
            f"{result.occurrences_moved} occurrence(s), "
            f"{result.references_moved} reference(s), "
            f"{result.relations_moved} relation(s); "
            f"deduplicated {result.references_deduplicated} reference(s) and "
            f"{result.relations_deduplicated} relation(s), "
            f"collapsed {result.relations_collapsed} direct relation(s).",
        )
    return result


def handle_edit(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    current = service.get_meaning(args.meaning_id)
    if _has_edit_values(args):
        name = args.name if args.name is not None else current.full_name
        description = (
            None
            if args.clear_description
            else args.description if args.description is not None else current.description
        )
    else:
        if args.json:
            message = "At least one of --name, --scope, or --description is required with --json."
            raise ValidationError(message)
        name, description = _prompt_for_edit(current)
    result = service.edit(args.meaning_id, name, description, args.scope)
    if not args.json:
        print(f"Updated meaning #{args.meaning_id}.")
    return result


def _has_edit_values(args: argparse.Namespace) -> bool:
    return (
        args.name is not None
        or args.scope is not None
        or args.description is not None
        or args.clear_description
    )


def _prompt_for_edit(current: Meaning) -> tuple[str, str | None]:
    name = input(f"Full name [{current.full_name}]: ").strip() or current.full_name
    entered = input(f"Description [{current.description or ''}]: ").strip()
    return name, entered or current.description


def handle_meanings(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.meanings(
        args.tag,
        scope=args.scope,
        favorite_only=args.favorite_only,
    )
    if not args.json:
        if result:
            for item in result:
                print_meaning(item)
        else:
            print("No meanings found.")
    return result
