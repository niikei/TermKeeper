"""Capture, inbox, occurrence, and analytics command handlers."""

import argparse
import sys

from termkeeper.adapters.cli.rendering import (
    print_has_more,
    print_inbox,
    print_meaning_candidates,
    print_occurrences,
    print_stats,
)
from termkeeper.adapters.cli.style import danger, heading, identifier, success, warning
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


def handle_add(args: argparse.Namespace, service: TermKeeperService) -> CaptureResult:
    result = service.add(
        args.keyword,
        args.memo,
        args.source,
        meaning_id=args.meaning_id,
    )
    if not args.json:
        occurrence = result.occurrence
        occurrence_id = identifier(f"#{occurrence.occurrence_id}")
        print(f"{success('Captured')} occurrence {occurrence_id}: {occurrence.keyword}")
        if occurrence.meaning_id is not None:
            meaning_id = identifier(f"#{occurrence.meaning_id}")
            print(f"{success('Assigned')} to meaning {meaning_id}.")
        elif result.candidates:
            print_meaning_candidates(result.candidates, heading="Possible meanings:")
            if not args.no_prompt and _can_prompt():
                selected_id = _prompt_for_immediate_assignment(result.candidates)
                if selected_id is not None:
                    assigned = service.assign(occurrence.occurrence_id, selected_id)
                    result = CaptureResult(assigned, result.candidates)
                    meaning_id = identifier(f"#{selected_id}")
                    print(
                        f"{success('Assigned')} occurrence {occurrence_id} to meaning {meaning_id}."
                    )
    return result


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _prompt_for_immediate_assignment(candidates: tuple[Meaning, ...]) -> int | None:
    candidate_ids = {candidate.meaning_id for candidate in candidates}
    while True:
        if len(candidates) == 1:
            candidate_id = candidates[0].meaning_id
            choice = identifier(f"#{candidate_id}")
            answer = input(f"Assign to {choice} now? [y/N]: ").strip()
            normalized = answer.casefold()
            if not answer or normalized in {"n", "no"}:
                return None
            if normalized in {"y", "yes"}:
                return candidate_id
        else:
            answer = input(
                "Meaning ID to assign now, or Enter to keep pending: ",
            ).strip()
            if not answer:
                return None
        try:
            selected_id = int(answer)
        except ValueError:
            print(warning("Please enter a displayed meaning ID or press Enter."))
            continue
        if selected_id in candidate_ids:
            return selected_id
        print(warning("Please choose one of the displayed meaning IDs."))


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


def handle_occurrence_search(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[OccurrenceItem]:
    result = service.search_occurrences(
        OccurrenceQuery(
            meaning_id=args.meaning_id,
            status=args.status,
            text=args.text,
            source=args.source,
            since=args.since,
            offset=args.offset,
            limit=args.limit,
        ),
    )
    if not args.json:
        print_occurrences(result.items)
        print_has_more(result)
    return result


def handle_inbox_search(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[OccurrenceItem]:
    result = service.search_inbox(
        OccurrenceQuery(
            text=args.text,
            source=args.source,
            since=args.since,
            offset=args.offset,
            limit=args.limit,
        ),
    )
    if not args.json:
        print_inbox(result.items)
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
        occurrence_id = identifier(f"#{args.occurrence_id}")
        print(f"{success('Updated')} occurrence {occurrence_id}.")
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
        if args.scope is not None or args.description is not None:
            message = "--scope and --description cannot be used with --meaning."
            raise ValidationError(message)
        assigned = service.assign(args.occurrence_id, args.meaning_id)
        if not args.json:
            occurrence_id = identifier(f"#{args.occurrence_id}")
            meaning_id = identifier(f"#{args.meaning_id}")
            print(
                f"{success('Assigned')} occurrence {occurrence_id} to meaning {meaning_id}.",
            )
        return assigned
    name = args.name
    description = args.description
    if name is None:
        if args.json:
            message = "--name is required with --json when creating a meaning."
            raise ValidationError(message)
        selected_id, name, description = _prompt_for_resolution(args, service)
        if selected_id is not None:
            assigned = service.assign(args.occurrence_id, selected_id)
            occurrence_id = identifier(f"#{args.occurrence_id}")
            meaning_id = identifier(f"#{selected_id}")
            print(
                f"{success('Assigned')} occurrence {occurrence_id} to meaning {meaning_id}.",
            )
            return assigned
    meaning = service.resolve(
        args.occurrence_id,
        name,
        description,
        args.scope or "General",
    )
    if not args.json:
        meaning_id = identifier(f"#{meaning.meaning_id}")
        print(f"{success('Created')} meaning {meaning_id}: {meaning.full_name}")
    return meaning


def handle_unresolve(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.unresolve(args.occurrence_id)
    if not args.json:
        occurrence_id = identifier(f"#{args.occurrence_id}")
        print(f"{warning('Returned')} occurrence {occurrence_id} to the inbox.")
    return result


def handle_discard(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.discard(args.occurrence_id)
    if not args.json:
        occurrence_id = identifier(f"#{args.occurrence_id}")
        print(f"{danger('Discarded')} occurrence {occurrence_id}.")
    return result


def handle_reopen(args: argparse.Namespace, service: TermKeeperService) -> OccurrenceItem:
    result = service.reopen(args.occurrence_id)
    if not args.json:
        occurrence_id = identifier(f"#{args.occurrence_id}")
        print(f"{success('Reopened')} occurrence {occurrence_id}.")
    return result


def _prompt_for_resolution(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> tuple[int | None, str, str | None]:
    options = service.resolution_options(args.occurrence_id)
    print(heading(f"Resolving: {options.occurrence.keyword}"))
    if options.candidates:
        print_meaning_candidates(options.candidates, heading="Matching meanings:")
        selected_id = _choose_candidate(options.candidates)
        if selected_id is not None:
            return selected_id, "", None
        print(warning("Creating a new meaning."))
    name = input("Full name: ").strip()
    if not name:
        message = "Resolution cancelled."
        raise ValidationError(message)
    description = args.description
    if description is None:
        description = input("Description: ").strip() or None
    return None, name, description


def _choose_candidate(candidates: tuple[Meaning, ...]) -> int | None:
    if len(candidates) == 1:
        candidate = candidates[0]
        answer = input(
            f"Press Enter to use #{candidate.meaning_id}, "
            "type 'n' for a new meaning, or 'q' to cancel: ",
        ).strip()
        if not answer:
            return candidate.meaning_id
    else:
        answer = input(
            "Enter a meaning ID, 'n' for a new meaning, or 'q' to cancel: ",
        ).strip()
    normalized = answer.casefold()
    if normalized in {"n", "new"}:
        return None
    if normalized in {"q", "quit"}:
        message = "Resolution cancelled."
        raise ValidationError(message)
    try:
        selected_id = int(answer)
    except ValueError as exc:
        message = f"Invalid meaning selection: {answer!r}."
        raise ValidationError(message) from exc
    if selected_id not in {candidate.meaning_id for candidate in candidates}:
        message = f"Meaning #{selected_id} is not one of the displayed candidates."
        raise ValidationError(message)
    return selected_id
