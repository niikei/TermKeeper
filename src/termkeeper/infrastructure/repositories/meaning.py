"""Persistence operations for meanings and aliases."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, select

from termkeeper.domain import SearchField
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.tables import Meaning, Scope, Term, utc_now


@dataclass(frozen=True, slots=True)
class MeaningValues:
    full_name: str
    scope_id: int
    description: str | None
    user_id: int | None


def create(
    session: Session,
    values: MeaningValues,
    *,
    public_id: UUID | None = None,
) -> Meaning:
    record = Meaning(
        full_name=values.full_name.strip(),
        full_name_norm=normalize_keyword(values.full_name),
        scope_id=values.scope_id,
        description=values.description or None,
        description_norm=normalize_keyword(values.description or ""),
        created_by_id=values.user_id,
        updated_by_id=values.user_id,
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


def get(session: Session, meaning_id: int, *, include_deleted: bool = False) -> Meaning | None:
    statement = select(Meaning).where(Meaning.meaning_id == meaning_id)
    if not include_deleted:
        statement = statement.where(col(Meaning.deleted_at).is_(None))
    return session.exec(statement).first()


def get_by_public_id(
    session: Session,
    public_id: UUID,
    *,
    include_deleted: bool = False,
) -> Meaning | None:
    statement = select(Meaning).where(Meaning.public_id == public_id)
    if not include_deleted:
        statement = statement.where(col(Meaning.deleted_at).is_(None))
    return session.exec(statement).first()


def get_public_ids(session: Session, meaning_ids: set[int]) -> dict[int, UUID]:
    if not meaning_ids:
        return {}
    rows = session.exec(
        select(Meaning.meaning_id, Meaning.public_id).where(
            col(Meaning.meaning_id).in_(meaning_ids),
        ),
    ).all()
    return {meaning_id: public_id for meaning_id, public_id in rows if meaning_id is not None}


def get_terms(session: Session, meaning_id: int) -> list[Term]:
    statement = select(Term).where(Term.meaning_id == meaning_id).order_by(Term.keyword_norm)
    return list(session.exec(statement).all())


def count_terms_to_move(session: Session, source_id: int, target_id: int) -> int:
    target_keywords = {term.keyword_norm for term in get_terms(session, target_id)}
    return sum(term.keyword_norm not in target_keywords for term in get_terms(session, source_id))


def move_terms(session: Session, source_id: int, target_id: int) -> int:
    target_keywords = {term.keyword_norm for term in get_terms(session, target_id)}
    source_terms = get_terms(session, source_id)
    for term in source_terms:
        if term.keyword_norm in target_keywords:
            session.delete(term)
    session.flush()
    moved = 0
    for term in source_terms:
        if term.keyword_norm not in target_keywords:
            term.meaning_id = target_id
            session.add(term)
            moved += 1
    return moved


def find_candidates(session: Session, keyword: str) -> list[Meaning]:
    statement = (
        select(Meaning)
        .join(Term)
        .join(Scope, col(Scope.scope_id) == col(Meaning.scope_id))
        .where(
            Term.keyword_norm == normalize_keyword(keyword),
            col(Meaning.deleted_at).is_(None),
        )
        .order_by(Scope.name_norm, Meaning.full_name_norm, col(Meaning.meaning_id))
    )
    return list(session.exec(statement).all())


def find_duplicate(
    session: Session,
    full_name: str,
    scope_id: int,
    *,
    exclude_id: int | None = None,
) -> Meaning | None:
    statement = select(Meaning).where(
        Meaning.full_name_norm == normalize_keyword(full_name),
        Meaning.scope_id == scope_id,
        col(Meaning.deleted_at).is_(None),
    )
    if exclude_id is not None:
        statement = statement.where(Meaning.meaning_id != exclude_id)
    return session.exec(statement).first()


def search(
    session: Session,
    tokens: tuple[str, ...],
    field: SearchField,
    *,
    scope_id: int | None = None,
    favorite_only: bool = False,
) -> list[Meaning]:
    token_conditions = [_search_condition(token, field) for token in tokens]
    statement = (
        select(Meaning)
        .outerjoin(Term)
        .where(or_(*token_conditions), col(Meaning.deleted_at).is_(None))
        .distinct()
        .order_by(col(Meaning.meaning_id))
    )
    if favorite_only:
        statement = statement.where(Meaning.is_favorite)
    if scope_id is not None:
        statement = statement.where(Meaning.scope_id == scope_id)
    return list(session.exec(statement).all())


def _search_condition(token: str, field: SearchField) -> ColumnElement[bool]:
    conditions: list[ColumnElement[bool]] = []
    if field in {SearchField.ALL, SearchField.TERM}:
        conditions.append(col(Term.keyword_norm).contains(token, autoescape=True))
    if field in {SearchField.ALL, SearchField.NAME}:
        conditions.append(col(Meaning.full_name_norm).contains(token, autoescape=True))
    if field in {SearchField.ALL, SearchField.DESCRIPTION}:
        conditions.append(col(Meaning.description_norm).contains(token, autoescape=True))
    return or_(*conditions)


def update(
    session: Session,
    record: Meaning,
    values: MeaningValues,
) -> None:
    record.full_name = values.full_name.strip()
    record.full_name_norm = normalize_keyword(values.full_name)
    record.scope_id = values.scope_id
    record.description = values.description or None
    record.description_norm = normalize_keyword(values.description or "")
    record.updated_at = utc_now()
    record.updated_by_id = values.user_id
    session.add(record)


def touch(session: Session, record: Meaning, user_id: int | None) -> None:
    record.updated_at = utc_now()
    record.updated_by_id = user_id
    session.add(record)


def set_favorite(
    session: Session,
    record: Meaning,
    user_id: int | None,
    *,
    favorite: bool,
) -> None:
    record.is_favorite = favorite
    touch(session, record, user_id)


def list_all(
    session: Session,
    *,
    scope_id: int | None = None,
    favorite_only: bool = False,
) -> list[Meaning]:
    statement = (
        select(Meaning)
        .where(col(Meaning.deleted_at).is_(None))
        .order_by(col(Meaning.updated_at).desc())
    )
    if favorite_only:
        statement = statement.where(Meaning.is_favorite)
    if scope_id is not None:
        statement = statement.where(Meaning.scope_id == scope_id)
    return list(session.exec(statement).all())


def list_deleted(session: Session) -> list[Meaning]:
    statement = (
        select(Meaning)
        .where(col(Meaning.deleted_at).is_not(None))
        .order_by(col(Meaning.deleted_at).desc())
    )
    return list(session.exec(statement).all())


def soft_delete(session: Session, record: Meaning, user_id: int | None) -> None:
    record.deleted_at = utc_now()
    record.deleted_by_id = user_id
    record.updated_at = record.deleted_at
    record.updated_by_id = user_id
    session.add(record)


def restore(session: Session, record: Meaning, user_id: int | None) -> None:
    record.deleted_at = None
    record.deleted_by_id = None
    record.updated_at = utc_now()
    record.updated_by_id = user_id
    session.add(record)


def purge(session: Session, record: Meaning) -> None:
    session.delete(record)
