"""CLI orchestration and shared error handling."""

import sys
import traceback
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from termkeeper.adapters.cli.types import CommandResult


def main(argv: Sequence[str] | None = None) -> int:
    from termkeeper.adapters.cli.parser import create_parser
    from termkeeper.adapters.cli.style import configure_color

    args = create_parser().parse_args(argv)
    configure_color("never" if args.json else args.color)
    if args.command == "completion":
        return _run_completion(args)

    from termkeeper.adapters.cli.handlers.registry import get_handler
    from termkeeper.application import (
        InitializationError,
        NotFoundError,
        TermKeeperService,
        ValidationError,
    )

    service = TermKeeperService()
    try:
        skip_initialization = args.command == "doctor" or (args.command == "init" and args.reset)
        if not skip_initialization:
            service.initialize()
        result = get_handler(args.command)(args, service)
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
            from termkeeper.adapters.cli.rendering import print_json

            print_json(result)
        return _exit_code(args.command, result)


def _run_completion(args: "Namespace") -> int:
    from termkeeper.adapters.cli.handlers.system import handle_completion
    from termkeeper.adapters.cli.rendering import print_json

    result = handle_completion(args, object())
    if args.json:
        print_json(result)
    return 0


def _exit_code(command: str, result: "CommandResult") -> int:
    if command == "doctor" and isinstance(result, Mapping) and result.get("status") == "error":
        return 1
    return 0


def _print_error(exc: Exception, *, json_output: bool) -> None:
    from termkeeper.adapters.cli.rendering import print_json
    from termkeeper.adapters.cli.style import danger

    if json_output:
        print_json({"error": type(exc).__name__, "message": str(exc)})
    else:
        print(danger(f"Error: {exc}", stream=sys.stderr), file=sys.stderr)
