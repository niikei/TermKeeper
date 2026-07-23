"""SQLModel persistence operations for meanings and terms."""

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.sqlite_utils import normalize_keyword, now
from termkeeper.infrastructure.tables import Meaning as MeaningRecord
from termkeeper.infrastructure.tables import Term as TermRecord


def create_meaning(full_name: str, description: str | None) -> int:
    stamp = now()
    record = MeaningRecord(
        full_name=full_name.strip(),
        description=description or None,
        created_at=stamp,
        updated_at=stamp,
    )
    with get_session() as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        if record.meaning_id is None:
            message = "SQLite did not return an ID for the inserted meaning."
            raise RuntimeError(message)
        return record.meaning_id


def add_term(meaning_id: int, keyword: str) -> bool:
    if not keyword.strip():
        return False
    stamp = now()
    record = TermRecord(
        meaning_id=meaning_id,
        keyword=keyword.strip(),
        keyword_norm=normalize_keyword(keyword),
        created_at=stamp,
        updated_at=stamp,
    )
    with get_session() as session:
        session.add(record)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return False
        return True


def get_meaning(meaning_id: int) -> MeaningRecord | None:
    with get_session() as session:
        return session.get(MeaningRecord, meaning_id)


def get_terms_by_meaning(meaning_id: int) -> list[TermRecord]:
    statement = (
        select(TermRecord)
        .where(TermRecord.meaning_id == meaning_id)
        .order_by(TermRecord.keyword_norm)
    )
    with get_session() as session:
        return list(session.exec(statement).all())


def meaning_exists(meaning_id: int) -> bool:
    return get_meaning(meaning_id) is not None


def find_registered_term(keyword: str) -> MeaningRecord | None:
    statement = (
        select(MeaningRecord)
        .join(TermRecord)
        .where(TermRecord.keyword_norm == normalize_keyword(keyword))
        .order_by(col(MeaningRecord.meaning_id))
    )
    with get_session() as session:
        return session.exec(statement).first()


def search_term(keyword: str) -> list[MeaningRecord]:
    pattern = f"%{normalize_keyword(keyword)}%"
    statement = (
        select(MeaningRecord)
        .outerjoin(TermRecord)
        .where(
            or_(
                col(TermRecord.keyword_norm).like(pattern),
                func.lower(MeaningRecord.full_name).like(pattern),
                func.lower(func.coalesce(MeaningRecord.description, "")).like(pattern),
            ),
        )
        .distinct()
        .order_by(MeaningRecord.full_name)
    )
    with get_session() as session:
        return list(session.exec(statement).all())


def update_meaning(meaning_id: int, full_name: str, description: str | None) -> int:
    with get_session() as session:
        record = session.get(MeaningRecord, meaning_id)
        if record is None:
            return 0
        record.full_name = full_name.strip()
        record.description = description or None
        record.updated_at = now()
        session.add(record)
        session.commit()
        return 1


def list_meanings() -> list[MeaningRecord]:
    statement = select(MeaningRecord).order_by(col(MeaningRecord.updated_at).desc())
    with get_session() as session:
        return list(session.exec(statement).all())


def list_meanings_for_export() -> list[MeaningRecord]:
    statement = select(MeaningRecord).order_by(col(MeaningRecord.meaning_id))
    with get_session() as session:
        return list(session.exec(statement).all())
