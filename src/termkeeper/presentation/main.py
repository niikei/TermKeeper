"""CLI orchestration and shared error handling."""

import sys
from collections.abc import Sequence

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.presentation.handlers import HANDLERS
from termkeeper.presentation.parser import create_parser
from termkeeper.presentation.rendering import print_json


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    service = TermKeeperService()
    service.initialize()
    try:
        result = HANDLERS[args.command](args, service)
    except (ValidationError, NotFoundError, ValueError, OSError) as exc:
        if args.json:
            print_json({"error": type(exc).__name__, "message": str(exc)})
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    else:
        if args.json:
            print_json(result)
        return 0
