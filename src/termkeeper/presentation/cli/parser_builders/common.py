"""Shared parser construction helpers."""

from __future__ import annotations

import argparse
from datetime import datetime


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Show meaningful defaults while preserving multiline examples."""

    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=30)

    def _get_help_string(self, action: argparse.Action) -> str:
        help_text = action.help or ""
        default = action.default
        if (
            action.option_strings
            and default not in {None, False, True, argparse.SUPPRESS}
            and "%(default)" not in help_text
        ):
            return f"{help_text} (default: %(default)s)"
        return help_text


class Commands:
    def __init__(
        self,
        parser: argparse.ArgumentParser,
        *,
        dest: str,
        required: bool = True,
        title: str = "Commands",
        metavar: str = "COMMAND",
    ) -> None:
        self._action = parser.add_subparsers(
            dest=dest,
            required=required,
            title=title,
            metavar=metavar,
        )

    def add(
        self,
        name: str,
        help_text: str,
        *,
        handler: str,
        description: str | None = None,
        examples: str | None = None,
    ) -> argparse.ArgumentParser:
        parser = self._action.add_parser(
            name,
            help=help_text,
            description=description or help_text,
            epilog=examples,
            formatter_class=HelpFormatter,
        )
        add_runtime_options(parser, suppress_default=True)
        parser.set_defaults(command=handler)
        return parser

    def group(self, name: str, help_text: str) -> Commands:
        parser = self._action.add_parser(
            name,
            help=help_text,
            description=help_text,
            formatter_class=HelpFormatter,
        )
        add_runtime_options(parser, suppress_default=True)
        parser.epilog = f"Run 'tk {name} ACTION --help' for action-specific help."
        return Commands(
            parser,
            dest=f"{name}_action",
            title="Actions",
            metavar="ACTION",
        )


def add_runtime_options(
    parser: argparse.ArgumentParser,
    *,
    suppress_default: bool = False,
) -> None:
    default = argparse.SUPPRESS if suppress_default else False
    parser.add_argument(
        "--json",
        action="store_true",
        default=default,
        help="Emit one machine-readable JSON value",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=default,
        help="Show technical details for unexpected errors",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default=argparse.SUPPRESS if suppress_default else "auto",
        help="Control ANSI colors",
    )


def add_pagination_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--offset", type=int, default=0, help="Rows to skip")
    parser.add_argument("--limit", type=int, default=50, help="Maximum rows")


def add_confirmation_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm the destructive operation without prompting",
    )


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        message = f"invalid ISO 8601 date or datetime: {value}"
        raise argparse.ArgumentTypeError(message) from exc
