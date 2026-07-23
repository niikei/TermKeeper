"""Shared persistence helpers for application use cases."""

from termkeeper.application.errors import NotFoundError
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    scope_repository,
)
from termkeeper.infrastructure.tables import Meaning, Occurrence, Scope, UserProfile
from termkeeper.infrastructure.unit_of_work import UnitOfWork


def get_occurrence(uow: UnitOfWork, occurrence_id: int) -> Occurrence:
    record = occurrence_repository.get(uow.session, occurrence_id)
    if record is None:
        message = f"Occurrence {occurrence_id} was not found."
        raise NotFoundError(message)
    return record


def get_meaning(uow: UnitOfWork, meaning_id: int) -> Meaning:
    record = meaning_repository.get(uow.session, meaning_id)
    if record is None:
        message = f"Meaning {meaning_id} was not found."
        raise NotFoundError(message)
    return record


def get_scope(uow: UnitOfWork, scope_id: int) -> Scope:
    record = scope_repository.get(uow.session, scope_id)
    if record is None:
        message = f"Scope {scope_id} was not found."
        raise NotFoundError(message)
    return record


def get_scope_by_name(uow: UnitOfWork, name: str) -> Scope:
    record = scope_repository.get_by_name(uow.session, name)
    if record is None:
        message = f"Scope '{name}' was not found. Create it with 'tk scope add'."
        raise NotFoundError(message)
    return record


def required_id(value: int | None) -> int:
    if value is None:  # pragma: no cover - guarded by the database identity invariant
        message = "A persisted record has no primary key."
        raise RuntimeError(message)
    return value


def user_id(profile: UserProfile | None) -> int | None:
    return required_id(profile.user_id) if profile is not None else None
