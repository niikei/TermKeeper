"""Shared application-boundary validation."""

from termkeeper.application.errors import ValidationError


def validate_page(
    offset: int,
    limit: int,
    *,
    resource: str,
    max_limit: int,
) -> None:
    if offset < 0:
        message = f"{resource} offset must not be negative."
        raise ValidationError(message)
    if not 1 <= limit <= max_limit:
        message = f"{resource} limit must be between 1 and {max_limit}."
        raise ValidationError(message)


def optional_filter(value: str | None, *, name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        message = f"{name} filter must not be empty."
        raise ValidationError(message)
    return normalized
