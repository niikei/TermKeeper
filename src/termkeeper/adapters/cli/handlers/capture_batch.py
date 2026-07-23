"""Human-oriented atomic batch capture handler."""

import argparse

from termkeeper.adapters.cli import batch_input
from termkeeper.adapters.cli.style import heading, identifier, success, warning
from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import CaptureBatchResult, CaptureInput


def handle_add_many(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> CaptureBatchResult:
    terms = batch_input.collect_terms(args.terms, args.file, json_output=args.json)
    if not args.json:
        _print_preview(terms)
        if batch_input.can_confirm() and not args.yes:
            answer = input("Capture these terms? [Y/n]: ").strip().casefold()
            if answer in {"n", "no"}:
                print(warning("Capture cancelled."))
                return CaptureBatchResult(())
            if answer not in {"", "y", "yes"}:
                message = "Please answer yes or no."
                raise ValidationError(message)
    result = service.capture_many(
        tuple(CaptureInput(term, args.memo, args.source) for term in terms),
    )
    if not args.json:
        _print_result(result)
    return result


def _print_preview(terms: tuple[str, ...]) -> None:
    print(heading(f"{len(terms)} terms to capture:"))
    for term in terms:
        print(f"  {term}")


def _print_result(result: CaptureBatchResult) -> None:
    print(success(f"Captured {len(result.items)} occurrences."))
    for item in result.items:
        occurrence = item.occurrence
        candidate_count = len(item.candidates)
        suffix = warning(f" ({candidate_count} possible meanings)") if candidate_count else ""
        print(f"  {identifier(f'#{occurrence.occurrence_id}')} {occurrence.keyword}{suffix}")
