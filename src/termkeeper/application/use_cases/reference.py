"""Meaning reference link use cases."""

from urllib.parse import urlsplit
from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.support import get_meaning, required_id, user_id
from termkeeper.application.validation import validate_page
from termkeeper.domain import Page, PageQuery, ReferenceLink, ReferenceUpdate
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    reference_repository,
    settings_repository,
)
from termkeeper.infrastructure.tables import MeaningReference
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class ReferenceUseCases:
    def reference_page(
        self,
        meaning_id: int,
        query: PageQuery | None = None,
    ) -> Page[ReferenceLink]:
        query = query or PageQuery()
        validate_page(query.offset, query.limit, resource="Reference", max_limit=100)
        with UnitOfWork() as uow:
            get_meaning(uow, meaning_id)
            records = reference_repository.list_page(
                uow.session,
                meaning_id,
                offset=query.offset,
                limit=query.limit,
            )
            return Page(
                items=tuple(_to_reference(record) for record in records[: query.limit]),
                offset=query.offset,
                limit=query.limit,
                has_more=len(records) > query.limit,
            )

    def references(self, meaning_id: int) -> list[ReferenceLink]:
        with UnitOfWork() as uow:
            get_meaning(uow, meaning_id)
            return [
                _to_reference(record)
                for record in reference_repository.list_for_meaning(uow.session, meaning_id)
            ]

    def add_reference(
        self,
        meaning_id: int,
        url: str,
        title: str | None = None,
    ) -> ReferenceLink:
        url = _validate_url(url)
        title = _optional_text(title)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            existing = reference_repository.find_by_url(uow.session, meaning_id, url)
            if existing is not None:
                return _to_reference(existing)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            record = reference_repository.create(uow.session, meaning_id, url, title, actor_id)
            meaning_repository.touch(uow.session, meaning, actor_id)
            result = _to_reference(record)
            uow.commit()
            return result

    def edit_reference(
        self,
        reference_id: int | UUID,
        update: ReferenceUpdate,
    ) -> ReferenceLink:
        _validate_update(update)
        with UnitOfWork() as uow:
            record = _get_reference(uow, reference_id)
            meaning = get_meaning(uow, record.meaning_id)
            url = _validate_url(update.url) if update.url is not None else record.url
            title = None if update.clear_title else _optional_text(update.title)
            if update.title is None and not update.clear_title:
                title = record.title
            duplicate = reference_repository.find_by_url(uow.session, record.meaning_id, url)
            if duplicate is not None and duplicate.reference_id != record.reference_id:
                message = f"Reference URL already exists for meaning {record.meaning_id}."
                raise ValidationError(message)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            reference_repository.update(uow.session, record, url, title, actor_id)
            meaning_repository.touch(uow.session, meaning, actor_id)
            result = _to_reference(record)
            uow.commit()
            return result

    def remove_reference(self, reference_id: int | UUID) -> ReferenceLink:
        with UnitOfWork() as uow:
            record = _get_reference(uow, reference_id)
            meaning = get_meaning(uow, record.meaning_id)
            result = _to_reference(record)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            reference_repository.remove(uow.session, record)
            meaning_repository.touch(uow.session, meaning, actor_id)
            uow.commit()
            return result


def _get_reference(
    uow: UnitOfWork,
    reference_id: int | UUID,
) -> MeaningReference:
    if isinstance(reference_id, UUID):
        record = reference_repository.get_by_public_id(uow.session, reference_id)
    else:
        record = reference_repository.get(uow.session, reference_id)
    if record is None:
        message = f"Reference {reference_id} was not found."
        raise NotFoundError(message)
    return record


def _validate_url(value: str) -> str:
    url = value.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        message = "Reference URL must be an absolute HTTP or HTTPS URL."
        raise ValidationError(message)
    return url


def _optional_text(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _validate_update(update: ReferenceUpdate) -> None:
    if update.url is None and update.title is None and not update.clear_title:
        message = "At least one reference field must be updated."
        raise ValidationError(message)
    if update.title is not None and update.clear_title:
        message = "Title and clear_title cannot be used together."
        raise ValidationError(message)


def _to_reference(record: MeaningReference) -> ReferenceLink:
    return ReferenceLink(
        reference_id=required_id(record.reference_id),
        public_id=record.public_id,
        meaning_id=record.meaning_id,
        url=record.url,
        title=record.title,
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
    )
