"""Meaning lifecycle and search command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import Meaning, MergeResult, SearchQuery, SearchResult
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
        for item in result:
            print_meaning(item)
    return result


def handle_restore(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.restore_meaning(args.meaning_id)
    if not args.json:
        print(f"Restored meaning #{args.meaning_id}.")
    return result


def handle_purge(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.purge_meaning(args.meaning_id)
    if not args.json:
        print(f"Permanently deleted meaning #{args.meaning_id}.")
    return {"purged": args.meaning_id}


def handle_merge(args: argparse.Namespace, service: TermKeeperService) -> MergeResult:
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
    name = args.name
    scope = args.scope
    description = args.description
    if name is None:
        name = input(f"Full name [{current.full_name}]: ").strip() or current.full_name
        if description is None:
            entered = input(f"Description [{current.description or ''}]: ").strip()
            description = entered or current.description
    result = service.edit(args.meaning_id, name, description, scope)
    if not args.json:
        print(f"Updated meaning #{args.meaning_id}.")
    return result


def handle_meanings(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.meanings(
        args.tag,
        scope=args.scope,
        favorite_only=args.favorite_only,
    )
    if not args.json:
        for item in result:
            print_meaning(item)
    return result
