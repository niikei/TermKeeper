"""Inbox capture and resolution use cases."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_inbox, to_meaning
from termkeeper.application.support import get_inbox, required_id, user_id
from termkeeper.domain import AddResult, InboxItem, InboxStatus, Meaning
from termkeeper.infrastructure.repositories import (
    inbox_repository,
    meaning_repository,
    settings_repository,
)
from termkeeper.infrastructure.tables import Meaning as MeaningRecord
from termkeeper.infrastructure.tables import utc_now
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class InboxUseCases:
    def add(self, keyword: str, memo: str | None = None, source: str | None = None) -> AddResult:
        keyword = keyword.strip()
        if not keyword:
            message = "Keyword must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            occurrence = inbox_repository.NewOccurrence(
                keyword,
                actor_id,
                memo=memo,
                source=source,
            )
            registered = meaning_repository.find_registered(uow.session, keyword)
            if registered is not None:
                result = _record_registered(uow, registered, occurrence)
            else:
                result = _record_inbox(uow, occurrence)
            uow.commit()
            return result

    def get_inbox(self, inbox_id: int) -> InboxItem:
        with UnitOfWork() as uow:
            return to_inbox(uow.session, get_inbox(uow, inbox_id))

    def get_inbox_by_public_id(self, public_id: UUID) -> InboxItem:
        with UnitOfWork() as uow:
            record = inbox_repository.get_inbox_by_public_id(uow.session, public_id)
            if record is None:
                message = f"Inbox {public_id} was not found."
                raise NotFoundError(message)
            return to_inbox(uow.session, record)

    def inbox(self) -> list[InboxItem]:
        with UnitOfWork() as uow:
            return [to_inbox(uow.session, row) for row in inbox_repository.list_inbox(uow.session)]

    def history(self) -> list[InboxItem]:
        with UnitOfWork() as uow:
            return [
                to_inbox(uow.session, row) for row in inbox_repository.list_history(uow.session)
            ]

    def edit_inbox(self, inbox_id: int, keyword: str) -> InboxItem:
        keyword = keyword.strip()
        if not keyword:
            message = "Keyword must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            inbox = get_inbox(uow, inbox_id)
            if inbox.status != InboxStatus.NEW:
                message = "Only open inbox items can be edited."
                raise ValidationError(message)
            duplicate = inbox_repository.find_open_inbox(uow.session, keyword)
            if duplicate is not None and duplicate.inbox_id != inbox.inbox_id:
                message = f"An open inbox already exists for '{keyword}'."
                raise ValidationError(message)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            inbox_repository.update_inbox(uow.session, inbox, keyword, actor_id)
            uow.session.flush()
            result = to_inbox(uow.session, inbox)
            uow.commit()
            return result

    def resolve(self, inbox_id: int, full_name: str, description: str | None = None) -> Meaning:
        if not full_name.strip():
            message = "Full name must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            inbox = get_inbox(uow, inbox_id)
            if inbox.status != InboxStatus.NEW:
                message = f"Inbox {inbox_id} is already {inbox.status}."
                raise ValidationError(message)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning = meaning_repository.create(uow.session, full_name, description, actor_id)
            meaning_id = required_id(meaning.meaning_id)
            meaning_repository.add_term(uow.session, meaning_id, inbox.keyword, actor_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, actor_id)
            inbox_repository.close(uow.session, inbox, InboxStatus.CLOSED, meaning_id)
            inbox_repository.link_occurrences(uow.session, inbox_id, meaning_id)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def discard(self, inbox_id: int) -> None:
        with UnitOfWork() as uow:
            inbox = get_inbox(uow, inbox_id)
            if inbox.status != InboxStatus.NEW:
                message = f"Open inbox {inbox_id} was not found."
                raise NotFoundError(message)
            inbox_repository.close(uow.session, inbox, InboxStatus.DISCARDED)
            uow.commit()


def _record_registered(
    uow: UnitOfWork,
    meaning: MeaningRecord,
    occurrence: inbox_repository.NewOccurrence,
) -> AddResult:
    meaning_id = required_id(meaning.meaning_id)
    inbox_repository.add_occurrence(
        uow.session,
        inbox_repository.NewOccurrence(
            occurrence.keyword,
            occurrence.user_id,
            meaning_id=meaning_id,
            memo=occurrence.memo,
            source=occurrence.source,
        ),
    )
    return AddResult("registered", meaning=to_meaning(uow.session, meaning))


def _record_inbox(
    uow: UnitOfWork,
    occurrence: inbox_repository.NewOccurrence,
) -> AddResult:
    inbox = inbox_repository.find_open_inbox(uow.session, occurrence.keyword)
    outcome = "seen_again" if inbox is not None else "created"
    if inbox is None:
        inbox = inbox_repository.add_inbox(uow.session, occurrence.keyword, occurrence.user_id)
    inbox_id = required_id(inbox.inbox_id)
    inbox.updated_at = utc_now()
    inbox_repository.add_occurrence(
        uow.session,
        inbox_repository.NewOccurrence(
            occurrence.keyword,
            occurrence.user_id,
            inbox_id=inbox_id,
            memo=occurrence.memo,
            source=occurrence.source,
        ),
    )
    uow.session.flush()
    return AddResult(outcome, inbox=to_inbox(uow.session, inbox))
