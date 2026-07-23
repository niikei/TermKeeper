"""Map persistence records to adapter-facing domain DTOs."""

from sqlmodel import Session

from termkeeper.application.support import required_id
from termkeeper.domain import InboxItem, OccurrenceItem
from termkeeper.domain import Meaning as MeaningDto
from termkeeper.infrastructure import inbox_repository, meaning_repository, tag_repository
from termkeeper.infrastructure.tables import Inbox, Meaning, Occurrence


def to_inbox(session: Session, record: Inbox) -> InboxItem:
    count, latest, memo, source = inbox_repository.occurrence_summary(
        session,
        required_id(record.inbox_id),
    )
    return InboxItem(
        inbox_id=required_id(record.inbox_id),
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


def to_meaning(session: Session, record: Meaning) -> MeaningDto:
    terms = tuple(
        term.keyword
        for term in meaning_repository.get_terms(session, required_id(record.meaning_id))
    )
    return MeaningDto(
        meaning_id=required_id(record.meaning_id),
        public_id=record.public_id,
        full_name=record.full_name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        terms=terms,
        tags=tuple(tag_repository.get_names(session, required_id(record.meaning_id))),
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
    )


def to_occurrence(record: Occurrence) -> OccurrenceItem:
    return OccurrenceItem(
        occurrence_id=required_id(record.occurrence_id),
        keyword=record.keyword,
        memo=record.memo,
        source=record.source,
        occurred_at=record.occurred_at,
        inbox_id=record.inbox_id,
        meaning_id=record.meaning_id,
        created_by_id=record.created_by_id,
    )
