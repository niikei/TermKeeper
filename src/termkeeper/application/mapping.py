"""Map persistence records to adapter-facing domain DTOs."""

from sqlmodel import Session

from termkeeper.application.support import required_id
from termkeeper.domain import Meaning as MeaningDto
from termkeeper.domain import OccurrenceItem
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    tag_repository,
)
from termkeeper.infrastructure.tables import Meaning, Occurrence


def to_meaning(session: Session, record: Meaning) -> MeaningDto:
    terms = tuple(
        term.keyword
        for term in meaning_repository.get_terms(session, required_id(record.meaning_id))
    )
    return MeaningDto(
        meaning_id=required_id(record.meaning_id),
        public_id=record.public_id,
        full_name=record.full_name,
        scope=record.scope,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
        is_favorite=record.is_favorite,
        terms=terms,
        tags=tuple(tag_repository.get_names(session, required_id(record.meaning_id))),
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
        deleted_by_id=record.deleted_by_id,
    )


def to_occurrence(record: Occurrence) -> OccurrenceItem:
    return OccurrenceItem(
        occurrence_id=required_id(record.occurrence_id),
        public_id=record.public_id,
        keyword=record.keyword,
        memo=record.memo,
        source=record.source,
        status=record.status,
        occurred_at=record.occurred_at,
        updated_at=record.updated_at,
        meaning_id=record.meaning_id,
        resolved_at=record.resolved_at,
        discarded_at=record.discarded_at,
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
        resolved_by_id=record.resolved_by_id,
        discarded_by_id=record.discarded_by_id,
    )
