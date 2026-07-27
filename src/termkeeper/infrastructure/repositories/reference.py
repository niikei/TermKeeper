"""Persistence operations for Meaning reference links."""

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, col, select

from termkeeper.infrastructure.tables import MeaningReference, utc_now


@dataclass(frozen=True, slots=True)
class MergePlan:
    moved: int
    deduplicated: int


def create(
    session: Session,
    meaning_id: int,
    url: str,
    title: str | None,
    user_id: int | None,
) -> MeaningReference:
    record = MeaningReference(
        meaning_id=meaning_id,
        url=url,
        title=title,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    session.add(record)
    session.flush()
    return record


def get(session: Session, reference_id: int) -> MeaningReference | None:
    return session.get(MeaningReference, reference_id)


def get_by_public_id(session: Session, public_id: UUID) -> MeaningReference | None:
    return session.exec(
        select(MeaningReference).where(MeaningReference.public_id == public_id),
    ).first()


def find_by_url(
    session: Session,
    meaning_id: int,
    url: str,
) -> MeaningReference | None:
    statement = select(MeaningReference).where(
        MeaningReference.meaning_id == meaning_id,
        MeaningReference.url == url,
    )
    return session.exec(statement).first()


def list_for_meaning(session: Session, meaning_id: int) -> list[MeaningReference]:
    statement = (
        select(MeaningReference)
        .where(MeaningReference.meaning_id == meaning_id)
        .order_by(col(MeaningReference.created_at), col(MeaningReference.reference_id))
    )
    return list(session.exec(statement).all())


def list_page(
    session: Session,
    meaning_id: int,
    *,
    offset: int,
    limit: int,
) -> list[MeaningReference]:
    statement = (
        select(MeaningReference)
        .where(MeaningReference.meaning_id == meaning_id)
        .order_by(col(MeaningReference.created_at), col(MeaningReference.reference_id))
        .offset(offset)
        .limit(limit + 1)
    )
    return list(session.exec(statement).all())


def plan_merge(session: Session, source_id: int, target_id: int) -> MergePlan:
    target_urls = {record.url for record in list_for_meaning(session, target_id)}
    source_records = list_for_meaning(session, source_id)
    deduplicated = sum(record.url in target_urls for record in source_records)
    return MergePlan(
        moved=len(source_records) - deduplicated,
        deduplicated=deduplicated,
    )


def move(
    session: Session,
    source_id: int,
    target_id: int,
    user_id: int | None,
) -> None:
    target_by_url = {record.url: record for record in list_for_meaning(session, target_id)}
    for source in list_for_meaning(session, source_id):
        target = target_by_url.get(source.url)
        if target is None:
            source.meaning_id = target_id
            session.add(source)
            continue
        _merge_duplicate(session, source, target, user_id)
    session.flush()


def update(
    session: Session,
    record: MeaningReference,
    url: str,
    title: str | None,
    user_id: int | None,
) -> None:
    record.url = url
    record.title = title
    record.updated_at = utc_now()
    record.updated_by_id = user_id
    session.add(record)


def remove(session: Session, record: MeaningReference) -> None:
    session.delete(record)


def _merge_duplicate(
    session: Session,
    source: MeaningReference,
    target: MeaningReference,
    user_id: int | None,
) -> None:
    if target.title is None and source.title is not None:
        target.title = source.title
        target.updated_at = utc_now()
        target.updated_by_id = user_id
        session.add(target)
    session.delete(source)
