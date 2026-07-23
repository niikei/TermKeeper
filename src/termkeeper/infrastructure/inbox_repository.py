"""Persistence operations for inbox items and occurrence history."""

from sqlmodel import Session, col, select

from termkeeper.domain.status import InboxStatus
from termkeeper.infrastructure.sqlite_utils import normalize_keyword
from termkeeper.infrastructure.tables import Inbox, Occurrence, utc_now


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
    keyword: str,
    user_id: int | None,
    *,
    inbox_id: int | None = None,
    meaning_id: int | None = None,
    memo: str | None = None,
    source: str | None = None,
) -> Occurrence:
    occurrence = Occurrence(
        keyword=keyword,
        inbox_id=inbox_id,
        meaning_id=meaning_id,
        memo=memo,
        source=source,
        created_by_id=user_id,
    )
    session.add(occurrence)
    return occurrence


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
