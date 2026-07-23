"""Safe human input handling for batch capture."""

import sys
from pathlib import Path

from termkeeper.application import ValidationError


def collect_terms(
    explicit: list[str] | None,
    file_path: str | None,
    *,
    json_output: bool,
) -> tuple[str, ...]:
    if explicit is not None:
        terms = tuple(explicit)
    elif file_path is not None:
        terms = _read_terms(file_path)
    elif json_output or not can_confirm():
        message = "Use --term or --file when add-many cannot prompt interactively."
        raise ValidationError(message)
    else:
        terms = _prompt_terms()
    if not terms:
        message = "At least one term is required."
        raise ValidationError(message)
    return terms


def can_confirm() -> bool:
    return sys.stdin.isatty()


def _read_terms(file_path: str) -> tuple[str, ...]:
    content = sys.stdin.read() if file_path == "-" else Path(file_path).read_text(encoding="utf-8")
    lines = content.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            message = f"Term file contains an empty value at line {line_number}."
            raise ValidationError(message)
    return tuple(lines)


def _prompt_terms() -> tuple[str, ...]:
    print("Enter terms, one per line. Submit an empty line to finish.")
    terms: list[str] = []
    while True:
        try:
            value = input("> ")
        except EOFError:
            break
        if not value:
            break
        terms.append(value)
    return tuple(terms)
