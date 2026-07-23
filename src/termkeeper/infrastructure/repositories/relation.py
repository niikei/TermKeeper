"""Persistence operations for symmetric Meaning relationships."""

from dataclasses import dataclass

from sqlalchemy import or_
from sqlmodel import Session, col, select

from termkeeper.infrastructure.tables import Meaning, MeaningRelation


@dataclass(frozen=True, slots=True)
class MergePlan:
    moved: int
    deduplicated: int
    collapsed: int


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
    relations = _list_records(session, meaning_id)
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


def plan_merge(session: Session, source_id: int, target_id: int) -> MergePlan:
    target_related_ids = _related_ids(_list_records(session, target_id), target_id)
    source_related_ids = _related_ids(_list_records(session, source_id), source_id)
    collapsed = int(target_id in source_related_ids)
    deduplicated = len((source_related_ids - {target_id}) & target_related_ids)
    moved = len(source_related_ids) - collapsed - deduplicated
    return MergePlan(
        moved=moved,
        deduplicated=deduplicated,
        collapsed=collapsed,
    )


def move(session: Session, source_id: int, target_id: int) -> None:
    target_related_ids = _related_ids(_list_records(session, target_id), target_id)
    for relation in _list_records(session, source_id):
        related_id = _other_id(relation, source_id)
        session.delete(relation)
        if related_id == target_id or related_id in target_related_ids:
            continue
        key = _key(target_id, related_id)
        session.add(
            MeaningRelation(
                meaning_id_low=key[0],
                meaning_id_high=key[1],
                created_at=relation.created_at,
                created_by_id=relation.created_by_id,
            ),
        )
        target_related_ids.add(related_id)
    session.flush()


def _key(meaning_id: int, related_id: int) -> tuple[int, int]:
    return min(meaning_id, related_id), max(meaning_id, related_id)


def _list_records(session: Session, meaning_id: int) -> list[MeaningRelation]:
    return list(
        session.exec(
            select(MeaningRelation).where(
                or_(
                    col(MeaningRelation.meaning_id_low) == meaning_id,
                    col(MeaningRelation.meaning_id_high) == meaning_id,
                ),
            ),
        ).all(),
    )


def _related_ids(
    relations: list[MeaningRelation],
    meaning_id: int,
) -> set[int]:
    return {_other_id(relation, meaning_id) for relation in relations}


def _other_id(relation: MeaningRelation, meaning_id: int) -> int:
    if relation.meaning_id_low == meaning_id:
        return relation.meaning_id_high
    return relation.meaning_id_low
