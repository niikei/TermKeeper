"""SQLModel persistence operations for inbox records."""

from sqlmodel import col, select

from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.sqlite_utils import normalize_keyword, now
from termkeeper.infrastructure.tables import Inbox as InboxRecord


def add_inbox(keyword: str, memo: str | None = None, source: str | None = None) -> int:
    stamp = now()
    record = InboxRecord(
        keyword=keyword.strip(),
        keyword_norm=normalize_keyword(keyword),
        memo=memo,
        source=source,
        created_at=stamp,
        updated_at=stamp,
        last_seen_at=stamp,
    )
    with get_session() as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        if record.inbox_id is None:
            message = "SQLite did not return an ID for the inserted inbox."
            raise RuntimeError(message)
        return record.inbox_id


def touch_inbox(inbox_id: int, memo: str | None = None, source: str | None = None) -> None:
    with get_session() as session:
        record = session.get(InboxRecord, inbox_id)
        if record is None:
            return
        stamp = now()
        record.occurrence_count += 1
        record.memo = memo if memo is not None else record.memo
        record.source = source if source is not None else record.source
        record.updated_at = record.last_seen_at = stamp
        session.add(record)
        session.commit()


def list_inbox() -> list[InboxRecord]:
    statement = (
        select(InboxRecord)
        .where(InboxRecord.status == "New")
        .order_by(col(InboxRecord.last_seen_at).desc(), col(InboxRecord.inbox_id).desc())
    )
    with get_session() as session:
        return list(session.exec(statement).all())


def list_history() -> list[InboxRecord]:
    statement = select(InboxRecord).order_by(
        col(InboxRecord.updated_at).desc(),
        col(InboxRecord.inbox_id).desc(),
    )
    with get_session() as session:
        return list(session.exec(statement).all())


def get_inbox(inbox_id: int) -> InboxRecord | None:
    with get_session() as session:
        return session.get(InboxRecord, inbox_id)


def find_open_inbox(keyword: str) -> InboxRecord | None:
    statement = (
        select(InboxRecord)
        .where(
            InboxRecord.keyword_norm == normalize_keyword(keyword),
            InboxRecord.status == "New",
        )
        .order_by(col(InboxRecord.inbox_id))
    )
    with get_session() as session:
        return session.exec(statement).first()


def close_inbox(inbox_id: int, meaning_id: int) -> int:
    return _close(inbox_id, "Closed", meaning_id)


def discard_inbox(inbox_id: int) -> int:
    return _close(inbox_id, "Discarded")


def _close(inbox_id: int, status: str, meaning_id: int | None = None) -> int:
    with get_session() as session:
        record = session.get(InboxRecord, inbox_id)
        if record is None or record.status != "New":
            return 0
        stamp = now()
        record.status = status
        record.resolved_meaning_id = meaning_id
        record.updated_at = record.closed_at = stamp
        session.add(record)
        session.commit()
        return 1
