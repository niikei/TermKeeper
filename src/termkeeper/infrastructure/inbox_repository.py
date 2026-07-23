"""Persistence operations for inbox items and occurrence history."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from termkeeper.domain import OccurrenceQuery
from termkeeper.domain.status import InboxStatus
from termkeeper.infrastructure.sqlite_utils import normalize_keyword
from termkeeper.infrastructure.tables import Inbox, Occurrence, utc_now


@dataclass(frozen=True, slots=True)
class NewOccurrence:
    keyword: str
    user_id: int | None
    inbox_id: int | None = None
    meaning_id: int | None = None
    memo: str | None = None
    source: str | None = None


def add_inbox(session: Session, keyword: str, user_id: int | None) -> Inbox:
    record = Inbox(
        keyword=keyword.strip(),
        keyword_norm=normalize_keyword(keyword),
        created_by_id=user_id,
    )
    session.add(record)
    session.flush()
    return record


def add_occurrence(
    session: Session,
    new: NewOccurrence,
) -> Occurrence:
    occurrence = Occurrence(
        keyword=new.keyword,
        keyword_norm=normalize_keyword(new.keyword),
        inbox_id=new.inbox_id,
        meaning_id=new.meaning_id,
        memo=new.memo,
        source=new.source,
        created_by_id=new.user_id,
    )
    session.add(occurrence)
    return occurrence


def list_occurrences(session: Session, query: OccurrenceQuery) -> list[Occurrence]:
    statement = select(Occurrence)
    if query.meaning_id is not None:
        statement = statement.where(Occurrence.meaning_id == query.meaning_id)
    if query.inbox_id is not None:
        statement = statement.where(Occurrence.inbox_id == query.inbox_id)
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
        statement = statement.where(Occurrence.occurred_at >= _sqlite_datetime(query.since))
    statement = statement.order_by(
        col(Occurrence.occurred_at).desc(),
        col(Occurrence.occurrence_id).desc(),
    ).limit(query.limit)
    return list(session.exec(statement).all())


def _sqlite_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=None)


def list_inbox(session: Session) -> list[Inbox]:
    statement = (
        select(Inbox)
        .where(Inbox.status == InboxStatus.NEW)
        .order_by(col(Inbox.updated_at).desc(), col(Inbox.inbox_id).desc())
    )
    return list(session.exec(statement).all())


def list_history(session: Session) -> list[Inbox]:
    statement = select(Inbox).order_by(col(Inbox.updated_at).desc(), col(Inbox.inbox_id).desc())
    return list(session.exec(statement).all())


def get_inbox(session: Session, inbox_id: int) -> Inbox | None:
    return session.get(Inbox, inbox_id)


def find_open_inbox(session: Session, keyword: str) -> Inbox | None:
    statement = select(Inbox).where(
        Inbox.keyword_norm == normalize_keyword(keyword),
        Inbox.status == InboxStatus.NEW,
    )
    return session.exec(statement).first()


def occurrence_summary(
    session: Session,
    inbox_id: int,
) -> tuple[int, Occurrence | None, str | None, str | None]:
    occurrences = session.exec(
        select(Occurrence)
        .where(Occurrence.inbox_id == inbox_id)
        .order_by(col(Occurrence.occurred_at).desc(), col(Occurrence.occurrence_id).desc()),
    ).all()
    latest = occurrences[0] if occurrences else None
    memo = next((item.memo for item in occurrences if item.memo is not None), None)
    source = next((item.source for item in occurrences if item.source is not None), None)
    return len(occurrences), latest, memo, source


def close(
    session: Session,
    record: Inbox,
    status: InboxStatus,
    meaning_id: int | None = None,
) -> None:
    record.status = status
    record.resolved_meaning_id = meaning_id
    record.updated_at = record.closed_at = utc_now()
    session.add(record)


def link_occurrences(session: Session, inbox_id: int, meaning_id: int) -> None:
    occurrences = session.exec(select(Occurrence).where(Occurrence.inbox_id == inbox_id)).all()
    for occurrence in occurrences:
        occurrence.meaning_id = meaning_id
        session.add(occurrence)


def count_meaning_references(session: Session, meaning_id: int) -> tuple[int, int]:
    occurrences = session.exec(
        select(Occurrence).where(Occurrence.meaning_id == meaning_id),
    ).all()
    inboxes = session.exec(
        select(Inbox).where(Inbox.resolved_meaning_id == meaning_id),
    ).all()
    return len(occurrences), len(inboxes)


def move_meaning_references(session: Session, source_id: int, target_id: int) -> tuple[int, int]:
    occurrences = session.exec(
        select(Occurrence).where(Occurrence.meaning_id == source_id),
    ).all()
    inboxes = session.exec(
        select(Inbox).where(Inbox.resolved_meaning_id == source_id),
    ).all()
    for occurrence in occurrences:
        occurrence.meaning_id = target_id
        session.add(occurrence)
    for inbox in inboxes:
        inbox.resolved_meaning_id = target_id
        session.add(inbox)
    return len(occurrences), len(inboxes)
