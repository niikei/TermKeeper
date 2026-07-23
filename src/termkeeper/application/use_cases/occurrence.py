"""Occurrence history use cases."""

from datetime import UTC, datetime

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_occurrence
from termkeeper.application.support import user_id
from termkeeper.domain import OccurrenceItem, OccurrenceQuery, OccurrenceUpdate
from termkeeper.infrastructure import inbox_repository, settings_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class OccurrenceUseCases:
    def occurrences(
        self,
        query: OccurrenceQuery | None = None,
    ) -> list[OccurrenceItem]:
        query = query or OccurrenceQuery()
        if not 1 <= query.limit <= 500:
            message = "Occurrence limit must be between 1 and 500."
            raise ValidationError(message)
        normalized = OccurrenceQuery(
            meaning_id=query.meaning_id,
            inbox_id=query.inbox_id,
            keyword=query.keyword.strip() if query.keyword else None,
            source=query.source.strip() if query.source else None,
            since=_to_utc(query.since),
            limit=query.limit,
        )
        with UnitOfWork() as uow:
            return [
                to_occurrence(row)
                for row in inbox_repository.list_occurrences(uow.session, normalized)
            ]

    def edit_occurrence(
        self,
        occurrence_id: int,
        update: OccurrenceUpdate,
    ) -> OccurrenceItem:
        _validate_update(update)
        with UnitOfWork() as uow:
            occurrence = inbox_repository.get_occurrence(uow.session, occurrence_id)
            if occurrence is None:
                message = f"Occurrence {occurrence_id} was not found."
                raise NotFoundError(message)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            inbox_repository.update_occurrence(uow.session, occurrence, update, actor_id)
            uow.session.flush()
            result = to_occurrence(occurrence)
            uow.commit()
            return result


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
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
