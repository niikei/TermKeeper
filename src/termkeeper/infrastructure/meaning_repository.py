"""Persistence operations for meanings and aliases."""

from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, select

from termkeeper.domain import SearchField
from termkeeper.infrastructure.sqlite_utils import normalize_keyword
from termkeeper.infrastructure.tables import Meaning, Term, utc_now


def create(
    session: Session,
    full_name: str,
    description: str | None,
    user_id: int | None,
    *,
    public_id: UUID | None = None,
) -> Meaning:
    record = Meaning(
        full_name=full_name.strip(),
        description=description or None,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    if public_id is not None:
        record.public_id = public_id
    session.add(record)
    session.flush()
    return record


def add_term(session: Session, meaning_id: int, keyword: str, user_id: int | None) -> bool:
    if not keyword.strip():
        return False
    existing = session.exec(
        select(Term).where(
            Term.meaning_id == meaning_id,
            Term.keyword_norm == normalize_keyword(keyword),
        ),
    ).first()
    if existing is not None:
        return False
    record = Term(
        meaning_id=meaning_id,
        keyword=keyword.strip(),
        keyword_norm=normalize_keyword(keyword),
        created_by_id=user_id,
    )
    session.add(record)
    return True


def remove_term(session: Session, meaning_id: int, keyword: str) -> bool:
    record = session.exec(
        select(Term).where(
            Term.meaning_id == meaning_id,
            Term.keyword_norm == normalize_keyword(keyword),
        ),
    ).first()
    if record is None:
        return False
    session.delete(record)
    return True


def get(session: Session, meaning_id: int) -> Meaning | None:
    return session.get(Meaning, meaning_id)


def get_by_public_id(session: Session, public_id: UUID) -> Meaning | None:
    return session.exec(select(Meaning).where(Meaning.public_id == public_id)).first()


def get_terms(session: Session, meaning_id: int) -> list[Term]:
    statement = select(Term).where(Term.meaning_id == meaning_id).order_by(Term.keyword_norm)
    return list(session.exec(statement).all())


def find_registered(session: Session, keyword: str) -> Meaning | None:
    statement = (
        select(Meaning)
        .join(Term)
        .where(Term.keyword_norm == normalize_keyword(keyword))
        .order_by(col(Meaning.meaning_id))
    )
    return session.exec(statement).first()


def search(
    session: Session,
    tokens: tuple[str, ...],
    field: SearchField,
) -> list[Meaning]:
    token_conditions = [_search_condition(token, field) for token in tokens]
    statement = (
        select(Meaning)
        .outerjoin(Term)
        .where(or_(*token_conditions))
        .distinct()
        .order_by(col(Meaning.meaning_id))
    )
    return list(session.exec(statement).all())


def _search_condition(token: str, field: SearchField) -> ColumnElement[bool]:
    conditions: list[ColumnElement[bool]] = []
    if field in {SearchField.ALL, SearchField.TERM}:
        conditions.append(col(Term.keyword_norm).contains(token, autoescape=True))
    if field in {SearchField.ALL, SearchField.NAME}:
        conditions.append(func.lower(Meaning.full_name).contains(token, autoescape=True))
    if field in {SearchField.ALL, SearchField.DESCRIPTION}:
        description = func.lower(func.coalesce(Meaning.description, ""))
        conditions.append(description.contains(token, autoescape=True))
    return or_(*conditions)


def update(
    session: Session,
    record: Meaning,
    full_name: str,
    description: str | None,
    user_id: int | None,
) -> None:
    record.full_name = full_name.strip()
    record.description = description or None
    record.updated_at = utc_now()
    record.updated_by_id = user_id
    session.add(record)


def list_all(session: Session) -> list[Meaning]:
    return list(session.exec(select(Meaning).order_by(col(Meaning.updated_at).desc())).all())


def delete(session: Session, record: Meaning) -> None:
    session.delete(record)
