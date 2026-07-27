"""Shared CLI interaction helpers."""

import argparse

from termkeeper.adapters.cli.style import danger
from termkeeper.application import ValidationError


def confirm_destructive(args: argparse.Namespace, message: str) -> None:
    if args.yes:
        return
    if args.json:
        error = "--yes is required with --json for destructive operations."
        raise ValidationError(error)
    answer = input(f"{danger(message)} [y/N]: ").strip().casefold()
    if answer not in {"y", "yes"}:
        error = "Operation cancelled."
        raise ValidationError(error)
