"""Capture, inbox, occurrence, and analytics command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    AddResult,
    InboxItem,
    Meaning,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceUpdate,
    StatsSummary,
)
from termkeeper.presentation.cli.rendering import (
    print_inbox,
    print_occurrences,
    print_stats,
)


def handle_add(args: argparse.Namespace, service: TermKeeperService) -> AddResult:
    result = service.add(args.keyword, args.memo, args.source)
    if args.json:
        return result
    if result.inbox is not None:
        if result.outcome == "created":
            print(f"Added inbox #{result.inbox.inbox_id}: {result.inbox.keyword}")
        else:
            print(
                f"Already in inbox #{result.inbox.inbox_id}; "
                f"seen count is now {result.inbox.occurrence_count}.",
            )
    elif result.meaning is not None:
        print(
            f"Already registered as meaning #{result.meaning.meaning_id}: "
            f"{result.meaning.full_name}",
        )
    return result


def handle_inbox(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.inbox()
    if not args.json:
        print_inbox(result)
    return result


def handle_history(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.history()
    if not args.json:
        print_inbox(result)
    return result


def handle_inbox_edit(args: argparse.Namespace, service: TermKeeperService) -> InboxItem:
    result = service.edit_inbox(args.inbox_id, args.keyword)
    if not args.json:
        print(f"Updated inbox #{args.inbox_id}: {result.keyword}")
    return result


def handle_occurrences(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> list[OccurrenceItem]:
    query = OccurrenceQuery(
        meaning_id=args.meaning_id,
        inbox_id=args.inbox_id,
        keyword=args.keyword,
        source=args.source,
        since=args.since,
        limit=args.limit,
    )
    result = service.occurrences(query)
    if not args.json:
        print_occurrences(result)
    return result


def handle_occurrence_edit(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> OccurrenceItem:
    update = OccurrenceUpdate(
        keyword=args.keyword,
        memo=args.memo,
        source=args.source,
        clear_memo=args.clear_memo,
        clear_source=args.clear_source,
    )
    result = service.edit_occurrence(args.occurrence_id, update)
    if not args.json:
        print(f"Updated occurrence #{args.occurrence_id}.")
    return result


def handle_stats(args: argparse.Namespace, service: TermKeeperService) -> StatsSummary:
    result = service.stats(args.limit)
    if not args.json:
        print_stats(result)
    return result


def handle_resolve(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    name = args.name
    description = args.description
    if name is None:
        item = service.get_inbox(args.inbox_id)
        print(f"Resolving: {item.keyword}")
        name = input("Full name: ").strip()
        if description is None:
            description = input("Description: ").strip() or None
    result = service.resolve(args.inbox_id, name, description)
    if not args.json:
        print(f"Created meaning #{result.meaning_id}: {result.full_name}")
    return result


def handle_discard(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.discard(args.inbox_id)
    if not args.json:
        print(f"Discarded inbox #{args.inbox_id}.")
    return {"discarded": args.inbox_id}
