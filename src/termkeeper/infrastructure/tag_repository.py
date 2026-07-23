"""Persistence operations for Meaning tags."""

from sqlalchemy import func
from sqlmodel import Session, col, select

from termkeeper.infrastructure.sqlite_utils import normalize_keyword
from termkeeper.infrastructure.tables import MeaningTag, Tag


def add(session: Session, meaning_id: int, name: str, user_id: int | None) -> bool:
    tag = _get_or_create(session, name, user_id)
    tag_id = _required_tag_id(tag)
    existing = session.get(MeaningTag, (meaning_id, tag_id))
    if existing is not None:
        return False
    session.add(MeaningTag(meaning_id=meaning_id, tag_id=tag_id, created_by_id=user_id))
    return True


def remove(session: Session, meaning_id: int, name: str) -> bool:
    tag = _get(session, name)
    if tag is None:
        return False
    tag_id = _required_tag_id(tag)
    link = session.get(MeaningTag, (meaning_id, tag_id))
    if link is None:
        return False
    session.delete(link)
    session.flush()
    remaining = session.exec(
        select(func.count()).select_from(MeaningTag).where(MeaningTag.tag_id == tag_id),
    ).one()
    if remaining == 0:
        session.delete(tag)
    return True


def get_names(session: Session, meaning_id: int) -> list[str]:
    statement = (
        select(Tag.name)
        .join(MeaningTag)
        .where(MeaningTag.meaning_id == meaning_id)
        .order_by(col(Tag.name_norm))
    )
    return list(session.exec(statement).all())


def list_summaries(session: Session) -> list[tuple[str, int]]:
    statement = (
        select(Tag.name, func.count(col(MeaningTag.meaning_id)))
        .join(MeaningTag)
        .group_by(col(Tag.tag_id))
        .order_by(col(Tag.name_norm))
    )
    return [(name, count) for name, count in session.exec(statement).all()]


def count_to_move(session: Session, source_id: int, target_id: int) -> int:
    target_tags = set(get_names(session, target_id))
    return sum(name not in target_tags for name in get_names(session, source_id))


def move(session: Session, source_id: int, target_id: int) -> int:
    target_tag_ids = set(
        session.exec(
            select(MeaningTag.tag_id).where(MeaningTag.meaning_id == target_id),
        ).all(),
    )
    source_links = list(
        session.exec(
            select(MeaningTag).where(MeaningTag.meaning_id == source_id),
        ).all(),
    )
    for link in source_links:
        if link.tag_id in target_tag_ids:
            session.delete(link)
    session.flush()
    moved = 0
    for link in source_links:
        if link.tag_id not in target_tag_ids:
            link.meaning_id = target_id
            session.add(link)
            moved += 1
    return moved


def _get_or_create(session: Session, name: str, user_id: int | None) -> Tag:
    existing = _get(session, name)
    if existing is not None:
        return existing
    tag = Tag(name=name.strip(), name_norm=normalize_keyword(name), created_by_id=user_id)
    session.add(tag)
    session.flush()
    return tag


def _get(session: Session, name: str) -> Tag | None:
    return session.exec(
        select(Tag).where(Tag.name_norm == normalize_keyword(name)),
    ).first()


def _required_tag_id(tag: Tag) -> int:
    if tag.tag_id is None:
        message = "A persisted tag has no primary key."
        raise RuntimeError(message)
    return tag.tag_id
