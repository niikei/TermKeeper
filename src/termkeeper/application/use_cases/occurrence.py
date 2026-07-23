"""Occurrence history use cases."""

from datetime import UTC, datetime
from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_occurrence
from termkeeper.application.support import user_id
from termkeeper.domain import (
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceStatus,
    OccurrenceUpdate,
    Page,
)
from termkeeper.infrastructure.repositories import occurrence_repository, settings_repository
from termkeeper.infrastructure.tables import Occurrence
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class OccurrenceUseCases:
    def occurrences(
        self,
        query: OccurrenceQuery | None = None,
    ) -> Page[OccurrenceItem]:
        query = query or OccurrenceQuery()
        if query.offset < 0:
            message = "Occurrence offset must not be negative."
            raise ValidationError(message)
        if not 1 <= query.limit <= 500:
            message = "Occurrence limit must be between 1 and 500."
            raise ValidationError(message)
        normalized = OccurrenceQuery(
            meaning_id=query.meaning_id,
            status=query.status,
            text=query.text.strip() if query.text else None,
            keyword=query.keyword.strip() if query.keyword else None,
            source=query.source.strip() if query.source else None,
            since=_to_utc(query.since),
            offset=query.offset,
            limit=query.limit,
        )
        with UnitOfWork() as uow:
            records = occurrence_repository.list_occurrences(uow.session, normalized)
            items = tuple(to_occurrence(row) for row in records[: normalized.limit])
            return Page(
                items=items,
                offset=normalized.offset,
                limit=normalized.limit,
                has_more=len(records) > normalized.limit,
            )

    def search_occurrences(self, query: OccurrenceQuery) -> Page[OccurrenceItem]:
        if query.text is None or not query.text.strip():
            message = "Occurrence search text must not be empty."
            raise ValidationError(message)
        return self.occurrences(query)

    def search_inbox(self, query: OccurrenceQuery) -> Page[OccurrenceItem]:
        return self.search_occurrences(
            OccurrenceQuery(
                status=OccurrenceStatus.PENDING,
                text=query.text,
                source=query.source,
                since=query.since,
                offset=query.offset,
                limit=query.limit,
            ),
        )

    def inbox(self, *, offset: int = 0, limit: int = 50) -> Page[OccurrenceItem]:
        return self.occurrences(
            OccurrenceQuery(
                status=OccurrenceStatus.PENDING,
                offset=offset,
                limit=limit,
            ),
        )

    def history(self, *, offset: int = 0, limit: int = 50) -> Page[OccurrenceItem]:
        return self.occurrences(OccurrenceQuery(offset=offset, limit=limit))

    def edit_occurrence(
        self,
        occurrence_id: int,
        update: OccurrenceUpdate,
    ) -> OccurrenceItem:
        _validate_update(update)
        with UnitOfWork() as uow:
            occurrence = occurrence_repository.get(uow.session, occurrence_id)
            if occurrence is None:
                message = f"Occurrence {occurrence_id} was not found."
                raise NotFoundError(message)
            return _update_occurrence(uow, occurrence, update)

    def edit_occurrence_by_public_id(
        self,
        public_id: UUID,
        update: OccurrenceUpdate,
    ) -> OccurrenceItem:
        _validate_update(update)
        with UnitOfWork() as uow:
            occurrence = occurrence_repository.get_by_public_id(
                uow.session,
                public_id,
            )
            if occurrence is None:
                message = f"Occurrence {public_id} was not found."
                raise NotFoundError(message)
            return _update_occurrence(uow, occurrence, update)


def _update_occurrence(
    uow: UnitOfWork,
    occurrence: Occurrence,
    update: OccurrenceUpdate,
) -> OccurrenceItem:
    actor_id = user_id(settings_repository.get_profile(uow.session))
    occurrence_repository.update(uow.session, occurrence, update, actor_id)
    uow.session.flush()
    result = to_occurrence(occurrence)
    uow.commit()
    return result


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_update(update: OccurrenceUpdate) -> None:
    if update.memo is not None and update.clear_memo:
        message = "memo and clear_memo cannot be specified together."
        raise ValidationError(message)
    if update.source is not None and update.clear_source:
        message = "source and clear_source cannot be specified together."
        raise ValidationError(message)
    if update.keyword is not None and not update.keyword.strip():
        message = "Keyword must not be empty."
        raise ValidationError(message)
    if update.memo is not None and not update.memo.strip():
        message = "Memo must not be empty; use clear_memo instead."
        raise ValidationError(message)
    if update.source is not None and not update.source.strip():
        message = "Source must not be empty; use clear_source instead."
        raise ValidationError(message)
    if all(value is None for value in (update.keyword, update.memo, update.source)) and not (
        update.clear_memo or update.clear_source
    ):
        message = "At least one occurrence field must be changed."
        raise ValidationError(message)
