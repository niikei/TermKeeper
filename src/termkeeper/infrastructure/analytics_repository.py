"""Read-only aggregate queries for usage analytics."""

from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, col, select

from termkeeper.domain.status import InboxStatus
from termkeeper.infrastructure.tables import Inbox, Meaning, Occurrence

type FrequencyRow = tuple[str, int, datetime]


def count_occurrences(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Occurrence)).one()


def count_open_inbox(session: Session) -> int:
    statement = (
        select(func.count()).select_from(Inbox).where(Inbox.status == InboxStatus.NEW)
    )
    return session.exec(statement).one()


def count_active_meanings(session: Session) -> int:
    statement = (
        select(func.count())
        .select_from(Meaning)
        .where(col(Meaning.deleted_at).is_(None))
    )
    return session.exec(statement).one()


def top_terms(session: Session, limit: int) -> list[FrequencyRow]:
    statement = (
        select(
            func.min(Occurrence.keyword),
            func.count(),
            func.max(Occurrence.occurred_at),
        )
        .group_by(Occurrence.keyword_norm)
        .order_by(func.count().desc(), func.max(Occurrence.occurred_at).desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def top_sources(session: Session, limit: int) -> list[FrequencyRow]:
    statement = (
        select(
            func.min(Occurrence.source),
            func.count(),
            func.max(Occurrence.occurred_at),
        )
        .where(col(Occurrence.source).is_not(None))
        .group_by(func.lower(Occurrence.source))
        .order_by(func.count().desc(), func.max(Occurrence.occurred_at).desc())
        .limit(limit)
    )
    return [
        (value, count, last_seen)
        for value, count, last_seen in session.exec(statement).all()
        if value is not None
    ]
