"""Persistence operations for symmetric Meaning relationships."""

from sqlalchemy import or_
from sqlmodel import Session, col, select

from termkeeper.infrastructure.tables import Meaning, MeaningRelation


def add(
    session: Session,
    meaning_id: int,
    related_id: int,
    user_id: int | None,
) -> bool:
    key = _key(meaning_id, related_id)
    if session.get(MeaningRelation, key) is not None:
        return False
    session.add(
        MeaningRelation(
            meaning_id_low=key[0],
            meaning_id_high=key[1],
            created_by_id=user_id,
        ),
    )
    return True


def remove(session: Session, meaning_id: int, related_id: int) -> bool:
    relation = session.get(MeaningRelation, _key(meaning_id, related_id))
    if relation is None:
        return False
    session.delete(relation)
    return True


def list_related(session: Session, meaning_id: int) -> list[Meaning]:
    relations = session.exec(
        select(MeaningRelation).where(
            or_(
                col(MeaningRelation.meaning_id_low) == meaning_id,
                col(MeaningRelation.meaning_id_high) == meaning_id,
            ),
        ),
    ).all()
    related_ids = [
        relation.meaning_id_high
        if relation.meaning_id_low == meaning_id
        else relation.meaning_id_low
        for relation in relations
    ]
    if not related_ids:
        return []
    statement = (
        select(Meaning)
        .where(
            col(Meaning.meaning_id).in_(related_ids),
            col(Meaning.deleted_at).is_(None),
        )
        .order_by(col(Meaning.full_name), col(Meaning.meaning_id))
    )
    return list(session.exec(statement).all())


def _key(meaning_id: int, related_id: int) -> tuple[int, int]:
    return min(meaning_id, related_id), max(meaning_id, related_id)
