"""Persistence operations for occurrence capture and classification."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, col, select

from termkeeper.domain import OccurrenceQuery, OccurrenceStatus, OccurrenceUpdate
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.tables import Occurrence, utc_now


@dataclass(frozen=True, slots=True)
class NewOccurrence:
    keyword: str
    user_id: int | None
    meaning_id: int | None = None
    memo: str | None = None
    source: str | None = None


def create(
    session: Session,
    new: NewOccurrence,
) -> Occurrence:
    status = OccurrenceStatus.RESOLVED if new.meaning_id is not None else OccurrenceStatus.PENDING
    occurrence = Occurrence(
        keyword=new.keyword,
        keyword_norm=normalize_keyword(new.keyword),
        status=status,
        meaning_id=new.meaning_id,
        memo=new.memo,
        source=new.source,
        created_by_id=new.user_id,
        resolved_at=utc_now() if new.meaning_id is not None else None,
        resolved_by_id=new.user_id if new.meaning_id is not None else None,
    )
    session.add(occurrence)
    session.flush()
    return occurrence


def get(session: Session, occurrence_id: int) -> Occurrence | None:
    return session.get(Occurrence, occurrence_id)


def get_by_public_id(
    session: Session,
    public_id: UUID,
) -> Occurrence | None:
    return session.exec(select(Occurrence).where(Occurrence.public_id == public_id)).first()


def update(
    session: Session,
    record: Occurrence,
    update: OccurrenceUpdate,
    user_id: int | None,
) -> None:
    if update.keyword is not None:
        record.keyword = update.keyword.strip()
        record.keyword_norm = normalize_keyword(update.keyword)
    if update.clear_memo:
        record.memo = None
    elif update.memo is not None:
        record.memo = update.memo.strip()
    if update.clear_source:
        record.source = None
    elif update.source is not None:
        record.source = update.source.strip()
    record.updated_at = utc_now()
    record.updated_by_id = user_id
    session.add(record)


def list_occurrences(session: Session, query: OccurrenceQuery) -> list[Occurrence]:
    statement = select(Occurrence)
    if query.meaning_id is not None:
        statement = statement.where(Occurrence.meaning_id == query.meaning_id)
    if query.status is not None:
        statement = statement.where(Occurrence.status == query.status)
    if query.keyword:
        statement = statement.where(
            col(Occurrence.keyword_norm).contains(
                normalize_keyword(query.keyword),
                autoescape=True,
            ),
        )
    if query.source:
        statement = statement.where(func.lower(Occurrence.source) == query.source.casefold())
    if query.since is not None:
        statement = statement.where(Occurrence.occurred_at >= query.since)
    statement = (
        statement.order_by(
            col(Occurrence.occurred_at).desc(),
            col(Occurrence.occurrence_id).desc(),
        )
        .offset(query.offset)
        .limit(query.limit + 1)
    )
    return list(session.exec(statement).all())


def assign(
    session: Session,
    record: Occurrence,
    meaning_id: int,
    user_id: int | None,
) -> None:
    now = utc_now()
    record.status = OccurrenceStatus.RESOLVED
    record.meaning_id = meaning_id
    record.resolved_at = now
    record.resolved_by_id = user_id
    record.discarded_at = None
    record.discarded_by_id = None
    record.updated_at = now
    record.updated_by_id = user_id
    session.add(record)


def unresolve(session: Session, record: Occurrence, user_id: int | None) -> None:
    now = utc_now()
    record.status = OccurrenceStatus.PENDING
    record.meaning_id = None
    record.resolved_at = None
    record.resolved_by_id = None
    record.discarded_at = None
    record.discarded_by_id = None
    record.updated_at = now
    record.updated_by_id = user_id
    session.add(record)


def discard(session: Session, record: Occurrence, user_id: int | None) -> None:
    now = utc_now()
    record.status = OccurrenceStatus.DISCARDED
    record.meaning_id = None
    record.resolved_at = None
    record.resolved_by_id = None
    record.discarded_at = now
    record.discarded_by_id = user_id
    record.updated_at = now
    record.updated_by_id = user_id
    session.add(record)


def count_meaning_references(session: Session, meaning_id: int) -> int:
    statement = (
        select(func.count()).select_from(Occurrence).where(Occurrence.meaning_id == meaning_id)
    )
    return session.exec(statement).one()


def move_meaning_references(session: Session, source_id: int, target_id: int) -> None:
    records = session.exec(
        select(Occurrence).where(Occurrence.meaning_id == source_id),
    ).all()
    for record in records:
        record.meaning_id = target_id
        session.add(record)
