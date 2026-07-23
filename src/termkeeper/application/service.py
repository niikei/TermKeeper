"""Transactional application use cases for CLI, HTTP, and MCP adapters."""

from uuid import UUID

from sqlmodel import Session

from termkeeper.domain import AddResult, InboxItem, InboxStatus, Meaning
from termkeeper.infrastructure import inbox_repository, meaning_repository, settings_repository
from termkeeper.infrastructure.schema import init_db
from termkeeper.infrastructure.tables import Inbox as InboxRecord
from termkeeper.infrastructure.tables import Meaning as MeaningRecord
from termkeeper.infrastructure.tables import UserProfile, utc_now
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class TermKeeperService:
    def initialize(self) -> None:
        init_db()

    def add(self, keyword: str, memo: str | None = None, source: str | None = None) -> AddResult:
        keyword = keyword.strip()
        if not keyword:
            message = "Keyword must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            user_id = _user_id(settings_repository.get_profile(uow.session))
            registered = meaning_repository.find_registered(uow.session, keyword)
            if registered is not None:
                meaning_id = _required_id(registered.meaning_id)
                inbox_repository.add_occurrence(
                    uow.session,
                    keyword,
                    user_id,
                    meaning_id=meaning_id,
                    memo=memo,
                    source=source,
                )
                result = AddResult("registered", meaning=_to_meaning(uow.session, registered))
            else:
                inbox = inbox_repository.find_open_inbox(uow.session, keyword)
                outcome = "seen_again" if inbox is not None else "created"
                if inbox is None:
                    inbox = inbox_repository.add_inbox(uow.session, keyword, user_id)
                inbox_id = _required_id(inbox.inbox_id)
                inbox.updated_at = utc_now()
                inbox_repository.add_occurrence(
                    uow.session,
                    keyword,
                    user_id,
                    inbox_id=inbox_id,
                    memo=memo,
                    source=source,
                )
                uow.session.flush()
                result = AddResult(outcome, inbox=_to_inbox(uow.session, inbox))
            uow.commit()
            return result

    def get_inbox(self, inbox_id: int) -> InboxItem:
        with UnitOfWork() as uow:
            record = _get_inbox(uow, inbox_id)
            return _to_inbox(uow.session, record)

    def inbox(self) -> list[InboxItem]:
        with UnitOfWork() as uow:
            return [_to_inbox(uow.session, row) for row in inbox_repository.list_inbox(uow.session)]

    def history(self) -> list[InboxItem]:
        with UnitOfWork() as uow:
            return [
                _to_inbox(uow.session, row) for row in inbox_repository.list_history(uow.session)
            ]

    def resolve(self, inbox_id: int, full_name: str, description: str | None = None) -> Meaning:
        if not full_name.strip():
            message = "Full name must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            inbox = _get_inbox(uow, inbox_id)
            if inbox.status != InboxStatus.NEW:
                message = f"Inbox {inbox_id} is already {inbox.status}."
                raise ValidationError(message)
            user_id = _user_id(settings_repository.get_profile(uow.session))
            meaning = meaning_repository.create(uow.session, full_name, description, user_id)
            meaning_id = _required_id(meaning.meaning_id)
            meaning_repository.add_term(uow.session, meaning_id, inbox.keyword, user_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, user_id)
            inbox_repository.close(uow.session, inbox, InboxStatus.CLOSED, meaning_id)
            inbox_repository.link_occurrences(uow.session, inbox_id, meaning_id)
            uow.session.flush()
            result = _to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def discard(self, inbox_id: int) -> None:
        with UnitOfWork() as uow:
            inbox = _get_inbox(uow, inbox_id)
            if inbox.status != InboxStatus.NEW:
                message = f"Open inbox {inbox_id} was not found."
                raise NotFoundError(message)
            inbox_repository.close(uow.session, inbox, InboxStatus.DISCARDED)
            uow.commit()

    def get_meaning(self, meaning_id: int) -> Meaning:
        with UnitOfWork() as uow:
            return _to_meaning(uow.session, _get_meaning(uow, meaning_id))

    def get_meaning_by_public_id(self, public_id: UUID) -> Meaning:
        with UnitOfWork() as uow:
            record = meaning_repository.get_by_public_id(uow.session, public_id)
            if record is None:
                message = f"Meaning {public_id} was not found."
                raise NotFoundError(message)
            return _to_meaning(uow.session, record)

    def create_meaning(
        self,
        full_name: str,
        description: str | None = None,
        terms: tuple[str, ...] = (),
        public_id: UUID | None = None,
    ) -> Meaning:
        if not full_name.strip():
            message = "Full name must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            user_id = _user_id(settings_repository.get_profile(uow.session))
            record = meaning_repository.create(
                uow.session,
                full_name,
                description,
                user_id,
                public_id=public_id,
            )
            meaning_id = _required_id(record.meaning_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, user_id)
            for term in terms:
                meaning_repository.add_term(uow.session, meaning_id, term, user_id)
            uow.session.flush()
            result = _to_meaning(uow.session, record)
            uow.commit()
            return result

    def search(self, keyword: str) -> list[Meaning]:
        if not keyword.strip():
            message = "Search keyword must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            return [
                _to_meaning(uow.session, row)
                for row in meaning_repository.search(uow.session, keyword)
            ]

    def meanings(self) -> list[Meaning]:
        with UnitOfWork() as uow:
            return [
                _to_meaning(uow.session, row) for row in meaning_repository.list_all(uow.session)
            ]

    def add_alias(self, meaning_id: int, keyword: str) -> Meaning:
        if not keyword.strip():
            message = "Alias must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            meaning = _get_meaning(uow, meaning_id)
            user_id = _user_id(settings_repository.get_profile(uow.session))
            meaning_repository.add_term(uow.session, meaning_id, keyword, user_id)
            uow.session.flush()
            result = _to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def remove_alias(self, meaning_id: int, keyword: str) -> Meaning:
        with UnitOfWork() as uow:
            meaning = _get_meaning(uow, meaning_id)
            if not meaning_repository.remove_term(uow.session, meaning_id, keyword):
                message = f"Alias '{keyword}' was not found."
                raise NotFoundError(message)
            uow.session.flush()
            result = _to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def edit(self, meaning_id: int, full_name: str, description: str | None) -> Meaning:
        if not full_name.strip():
            message = "Full name must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            meaning = _get_meaning(uow, meaning_id)
            user_id = _user_id(settings_repository.get_profile(uow.session))
            meaning_repository.update(uow.session, meaning, full_name, description, user_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, user_id)
            uow.session.flush()
            result = _to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def delete_meaning(self, meaning_id: int) -> None:
        with UnitOfWork() as uow:
            meaning_repository.delete(uow.session, _get_meaning(uow, meaning_id))
            uow.commit()

    def set_config(self, key: str, value: str) -> dict[str, str]:
        _validate_config(key, value)
        with UnitOfWork() as uow:
            profile = settings_repository.set_value(uow.session, key, value.strip())
            uow.commit()
            return {"key": key, "value": settings_repository.as_config(profile)[key]}

    def get_config(self, key: str) -> dict[str, str]:
        _validate_config_key(key)
        with UnitOfWork() as uow:
            config = settings_repository.as_config(settings_repository.get_profile(uow.session))
            if key not in config:
                message = f"Configuration '{key}' was not found."
                raise NotFoundError(message)
            return {"key": key, "value": config[key]}

    def list_config(self) -> dict[str, str]:
        with UnitOfWork() as uow:
            return settings_repository.as_config(settings_repository.get_profile(uow.session))

    def unset_config(self, key: str) -> dict[str, str]:
        _validate_config_key(key)
        with UnitOfWork() as uow:
            profile = settings_repository.unset_value(uow.session, key)
            uow.commit()
            return settings_repository.as_config(profile)


def _get_inbox(uow: UnitOfWork, inbox_id: int) -> InboxRecord:
    record = inbox_repository.get_inbox(uow.session, inbox_id)
    if record is None:
        message = f"Inbox {inbox_id} was not found."
        raise NotFoundError(message)
    return record


def _get_meaning(uow: UnitOfWork, meaning_id: int) -> MeaningRecord:
    record = meaning_repository.get(uow.session, meaning_id)
    if record is None:
        message = f"Meaning {meaning_id} was not found."
        raise NotFoundError(message)
    return record


def _required_id(value: int | None) -> int:
    if value is None:
        message = "A persisted record has no primary key."
        raise RuntimeError(message)
    return value


def _user_id(profile: UserProfile | None) -> int | None:
    return _required_id(profile.user_id) if profile is not None else None


def _to_inbox(session: Session, record: InboxRecord) -> InboxItem:
    count, latest, memo, source = inbox_repository.occurrence_summary(
        session,
        _required_id(record.inbox_id),
    )
    return InboxItem(
        inbox_id=_required_id(record.inbox_id),
        keyword=record.keyword,
        status=record.status,
        memo=memo,
        source=source,
        occurrence_count=count,
        created_at=record.created_at,
        updated_at=record.updated_at,
        last_seen_at=latest.occurred_at if latest else record.created_at,
        closed_at=record.closed_at,
        resolved_meaning_id=record.resolved_meaning_id,
        created_by_id=record.created_by_id,
    )


def _to_meaning(session: Session, record: MeaningRecord) -> Meaning:
    terms = tuple(
        term.keyword
        for term in meaning_repository.get_terms(session, _required_id(record.meaning_id))
    )
    return Meaning(
        meaning_id=_required_id(record.meaning_id),
        public_id=record.public_id,
        full_name=record.full_name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        terms=terms,
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
    )


def _validate_config(key: str, value: str) -> None:
    _validate_config_key(key)
    if not value.strip():
        message = f"Configuration '{key}' must not be empty."
        raise ValidationError(message)
    if key == "user.email" and ("@" not in value or value.startswith("@") or value.endswith("@")):
        message = "user.email must be a valid email address."
        raise ValidationError(message)


def _validate_config_key(key: str) -> None:
    if key not in {"user.name", "user.email"}:
        message = f"Unsupported configuration key: {key}"
        raise ValidationError(message)
