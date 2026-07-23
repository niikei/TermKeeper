"""Shared persistence helpers for application use cases."""

from termkeeper.application.errors import NotFoundError
from termkeeper.infrastructure import inbox_repository, meaning_repository
from termkeeper.infrastructure.tables import Inbox, Meaning, UserProfile
from termkeeper.infrastructure.unit_of_work import UnitOfWork


def get_inbox(uow: UnitOfWork, inbox_id: int) -> Inbox:
    record = inbox_repository.get_inbox(uow.session, inbox_id)
    if record is None:
        message = f"Inbox {inbox_id} was not found."
        raise NotFoundError(message)
    return record


def get_meaning(uow: UnitOfWork, meaning_id: int) -> Meaning:
    record = meaning_repository.get(uow.session, meaning_id)
    if record is None:
        message = f"Meaning {meaning_id} was not found."
        raise NotFoundError(message)
    return record


def required_id(value: int | None) -> int:
    if value is None:
        message = "A persisted record has no primary key."
        raise RuntimeError(message)
    return value


def user_id(profile: UserProfile | None) -> int | None:
    return required_id(profile.user_id) if profile is not None else None
