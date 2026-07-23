"""Capture, inbox, occurrence, and analytics command handlers."""

import argparse

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import (
    CaptureResult,
    Meaning,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceUpdate,
    Page,
    StatsSummary,
)
from termkeeper.presentation.cli.rendering import (
    print_has_more,
    print_inbox,
    print_occurrences,
    print_stats,
)


def handle_add(args: argparse.Namespace, service: TermKeeperService) -> CaptureResult:
    result = service.add(
        args.keyword,
        args.memo,
        args.source,
        meaning_id=args.meaning_id,
    )
    if not args.json:
        occurrence = result.occurrence
        print(f"Captured occurrence #{occurrence.occurrence_id}: {occurrence.keyword}")
        if occurrence.meaning_id is not None:
            print(f"Assigned to meaning #{occurrence.meaning_id}.")
        elif result.candidates:
            print("Possible meanings:")
            for candidate in result.candidates:
                print(
                    f"  #{candidate.meaning_id} [{candidate.scope}] {candidate.full_name}",
                )
    return result


def handle_inbox(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[OccurrenceItem]:
    result = service.inbox(offset=args.offset, limit=args.limit)
    if not args.json:
        print_inbox(result.items)
        print_has_more(result)
    return result


def handle_history(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[OccurrenceItem]:
    result = service.history(offset=args.offset, limit=args.limit)
    if not args.json:
        print_occurrences(result.items)
        print_has_more(result)
    return result


def handle_occurrences(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[OccurrenceItem]:
    query = OccurrenceQuery(
        meaning_id=args.meaning_id,
        status=args.status,
        keyword=args.keyword,
        source=args.source,
        since=args.since,
        offset=args.offset,
        limit=args.limit,
    )
    result = service.occurrences(query)
    if not args.json:
        print_occurrences(result.items)
        print_has_more(result)
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


def handle_resolve(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Meaning | OccurrenceItem:
    if args.meaning_id is not None:
        assigned = service.assign(args.occurrence_id, args.meaning_id)
        if not args.json:
            print(
                f"Assigned occurrence #{args.occurrence_id} to meaning #{args.meaning_id}.",
            )
        return assigned
    name = args.name
    description = args.description
    if name is None:
        if args.json:
            message = "--name is required with --json when creating a meaning."
            raise ValidationError(message)
        name, description = _prompt_for_resolution(args, service)
    meaning = service.resolve(args.occurrence_id, name, description, args.scope)
    if not args.json:
        print(f"Created meaning #{meaning.meaning_id}: {meaning.full_name}")
    return meaning


def handle_unresolve(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.unresolve(args.occurrence_id)
    if not args.json:
        print(f"Returned occurrence #{args.occurrence_id} to the inbox.")
    return result


def handle_discard(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.discard(args.occurrence_id)
    if not args.json:
        print(f"Discarded occurrence #{args.occurrence_id}.")
    return result


def handle_reopen(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.reopen(args.occurrence_id)
    if not args.json:
        print(f"Reopened occurrence #{args.occurrence_id}.")
    return result


def _prompt_for_resolution(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> tuple[str, str | None]:
    item = service.get_occurrence(args.occurrence_id)
    print(f"Resolving: {item.keyword}")
    name = input("Full name: ").strip()
    description = args.description
    if description is None:
        description = input("Description: ").strip() or None
    return name, description
