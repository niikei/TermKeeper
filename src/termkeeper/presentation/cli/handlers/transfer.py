"""Initialization and data transfer command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import ImportResult
from termkeeper.infrastructure.schema import reset_sqlite_database
from termkeeper.presentation.cli.handlers.common import confirm_destructive
from termkeeper.presentation.cli.style import command, danger, success, warning
from termkeeper.presentation.csv_io import export_meanings, import_meanings


def handle_init(args: argparse.Namespace, _service: TermKeeperService) -> dict[str, str]:
    if args.reset:
        confirm_destructive(
            args,
            "Back up and recreate the configured SQLite database?",
        )
        backup = reset_sqlite_database()
        backup_text = str(backup) if backup is not None else "none"
        if not args.json:
            print(success("Database recreated."))
            if backup is not None:
                print(f"Backup: {command(str(backup))}")
        return {"status": "reset", "backup": backup_text}
    if not args.json:
        print(success("Database initialized and up to date."))
    return {"status": "ok"}


def handle_export(
    args: argparse.Namespace,
    _service: TermKeeperService,
) -> dict[str, str | int]:
    count = export_meanings(args.path, _service)
    if not args.json:
        print(f"{success('Exported')} {count} meaning(s) to {command(args.path)}.")
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
        styled_action = warning(action) if result.dry_run else success(action)
        print(
            f"{styled_action} {result.created}, updated {result.updated}, "
            f"skipped {warning(str(result.skipped))}.",
        )
        for issue in result.issues:
            print(danger(f"Row {issue.row_number}: {issue.message}"))
    return result
