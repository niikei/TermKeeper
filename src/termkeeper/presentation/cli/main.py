"""CLI orchestration and shared error handling."""

import sys
import traceback
from collections.abc import Sequence

from termkeeper.application import (
    InitializationError,
    NotFoundError,
    TermKeeperService,
    ValidationError,
)
from termkeeper.presentation.cli.handlers.registry import HANDLERS
from termkeeper.presentation.cli.parser import create_parser
from termkeeper.presentation.cli.rendering import print_json


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    service = TermKeeperService()
    try:
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
        return 0


def _print_error(exc: Exception, *, json_output: bool) -> None:
    if json_output:
        print_json({"error": type(exc).__name__, "message": str(exc)})
    else:
        print(f"Error: {exc}", file=sys.stderr)
