"""CLI orchestration and shared error handling."""

import sys
import traceback
from collections.abc import Mapping, Sequence

from termkeeper.adapters.cli.handlers.registry import HANDLERS
from termkeeper.adapters.cli.parser import create_parser
from termkeeper.adapters.cli.rendering import print_json
from termkeeper.adapters.cli.style import configure_color, danger
from termkeeper.adapters.cli.types import CommandResult
from termkeeper.application import (
    InitializationError,
    NotFoundError,
    TermKeeperService,
    ValidationError,
)


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    configure_color("never" if args.json else args.color)
    service = TermKeeperService()
    try:
        skip_initialization = args.command in {"completion", "doctor"} or (
            args.command == "init" and args.reset
        )
        if not skip_initialization:
            service.initialize()
        result = HANDLERS[args.command](args, service)
    except InitializationError as exc:
        if args.debug:
            traceback.print_exc()
        _print_error(exc, json_output=args.json)
        return 1
    except (ValidationError, NotFoundError, ValueError, OSError) as exc:
        _print_error(exc, json_output=args.json)
        return 2
    else:
        if args.json:
            print_json(result)
        return _exit_code(args.command, result)


def _exit_code(command: str, result: CommandResult) -> int:
    if command == "doctor" and isinstance(result, Mapping) and result.get("status") == "error":
        return 1
    return 0


def _print_error(exc: Exception, *, json_output: bool) -> None:
    if json_output:
        print_json({"error": type(exc).__name__, "message": str(exc)})
    else:
        print(danger(f"Error: {exc}", stream=sys.stderr), file=sys.stderr)
