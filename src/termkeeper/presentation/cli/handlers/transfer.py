"""Initialization and data transfer command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import ImportResult
from termkeeper.presentation.csv_io import export_meanings, import_meanings


def handle_init(args: argparse.Namespace, _service: TermKeeperService) -> dict[str, str]:
    if not args.json:
        print("Database initialized and up to date.")
    return {"status": "ok"}


def handle_export(
    args: argparse.Namespace,
    _service: TermKeeperService,
) -> dict[str, str | int]:
    count = export_meanings(args.path, _service)
    if not args.json:
        print(f"Exported {count} meaning(s) to {args.path}.")
    return {"exported": count, "path": args.path}


def handle_import(args: argparse.Namespace, service: TermKeeperService) -> ImportResult:
    result = import_meanings(
        args.path,
        service,
        dry_run=args.dry_run,
        strict=args.strict,
    )
    if not args.json:
        action = "Would create" if result.dry_run else "Created"
        print(
            f"{action} {result.created}, updated {result.updated}, skipped {result.skipped}.",
        )
        for issue in result.issues:
            print(f"Row {issue.row_number}: {issue.message}")
    return result
