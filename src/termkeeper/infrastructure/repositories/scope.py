"""Persistence operations for meaning scopes."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.tables import Meaning, Scope, utc_now


@dataclass(frozen=True, slots=True)
class ScopeValues:
    name: str
    description: str | None
    user_id: int | None


def create(session: Session, values: ScopeValues) -> Scope:
    record = Scope(
        name=values.name.strip(),
        name_norm=normalize_keyword(values.name),
        description=values.description.strip() if values.description else None,
        created_by_id=values.user_id,
        updated_by_id=values.user_id,
    )
    session.add(record)
    session.flush()
    return record


def get(session: Session, scope_id: int) -> Scope | None:
    return session.get(Scope, scope_id)


def get_by_name(session: Session, name: str) -> Scope | None:
    return session.exec(
        select(Scope).where(Scope.name_norm == normalize_keyword(name)),
    ).first()


def get_by_public_id(session: Session, public_id: UUID) -> Scope | None:
    return session.exec(select(Scope).where(Scope.public_id == public_id)).first()


def list_all(session: Session) -> list[Scope]:
    return list(session.exec(select(Scope).order_by(col(Scope.name_norm))).all())


def list_page(
    session: Session,
    *,
    offset: int,
    limit: int,
) -> list[Scope]:
    statement = (
        select(Scope)
        .order_by(col(Scope.name_norm), col(Scope.scope_id))
        .offset(offset)
        .limit(limit + 1)
    )
    return list(session.exec(statement).all())


def search(
    session: Session,
    text: str,
    *,
    offset: int,
    limit: int,
) -> list[Scope]:
    normalized = normalize_keyword(text)
    statement = (
        select(Scope)
        .where(
            or_(
                col(Scope.name_norm).contains(normalized, autoescape=True),
                func.lower(Scope.description).contains(text.casefold(), autoescape=True),
            ),
        )
        .order_by(col(Scope.name_norm), col(Scope.scope_id))
        .offset(offset)
        .limit(limit + 1)
    )
    return list(session.exec(statement).all())


def update(session: Session, record: Scope, values: ScopeValues) -> None:
    record.name = values.name.strip()
    record.name_norm = normalize_keyword(values.name)
    record.description = values.description.strip() if values.description else None
    record.updated_at = utc_now()
    record.updated_by_id = values.user_id
    session.add(record)


def count_meanings(session: Session, scope_id: int) -> int:
    return session.exec(
        select(func.count()).select_from(Meaning).where(Meaning.scope_id == scope_id),
    ).one()


def remove(session: Session, record: Scope) -> None:
    session.delete(record)
