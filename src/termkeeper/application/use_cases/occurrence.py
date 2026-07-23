"""Occurrence history use cases."""

from datetime import UTC, datetime

from termkeeper.application.errors import ValidationError
from termkeeper.application.mapping import to_occurrence
from termkeeper.domain import OccurrenceItem, OccurrenceQuery
from termkeeper.infrastructure import inbox_repository
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


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(UTC)
