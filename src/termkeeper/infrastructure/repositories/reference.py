"""Persistence operations for Meaning reference links."""

from sqlmodel import Session, col, select

from termkeeper.infrastructure.tables import MeaningReference, utc_now


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
