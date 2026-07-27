"""Shared validation helpers for Meaning write use cases."""

from termkeeper.application.errors import ValidationError
from termkeeper.infrastructure.repositories import meaning_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


def validate_meaning_name(full_name: str) -> None:
    if not full_name.strip():
        message = "Full name must not be empty."
        raise ValidationError(message)


def ensure_unique_meaning(
    uow: UnitOfWork,
    full_name: str,
    scope_id: int,
    scope_name: str,
    *,
    exclude_id: int | None = None,
) -> None:
    duplicate = meaning_repository.find_duplicate(
        uow.session,
        full_name,
        scope_id,
        exclude_id=exclude_id,
    )
    if duplicate is not None:
        message = f"Meaning '{full_name}' already exists in scope '{scope_name}'."
        raise ValidationError(message)
