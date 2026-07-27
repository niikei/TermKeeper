"""Map persistence records to adapter-facing domain DTOs."""

from collections.abc import Mapping, Sequence

from sqlmodel import Session

from termkeeper.application.support import required_id
from termkeeper.domain import Meaning as MeaningDto
from termkeeper.domain import OccurrenceItem
from termkeeper.domain import Scope as ScopeDto
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    scope_repository,
    tag_repository,
)
from termkeeper.infrastructure.tables import Meaning, Occurrence, Scope


def to_meaning(session: Session, record: Meaning) -> MeaningDto:
    return to_meanings(session, (record,))[0]


def to_meanings(
    session: Session,
    records: Sequence[Meaning],
    *,
    term_names: Mapping[int, tuple[str, ...]] | None = None,
) -> tuple[MeaningDto, ...]:
    if not records:
        return ()
    meaning_ids = {required_id(record.meaning_id) for record in records}
    scopes = scope_repository.get_many(
        session,
        {record.scope_id for record in records},
    )
    terms = (
        meaning_repository.get_term_names(session, meaning_ids)
        if term_names is None
        else term_names
    )
    tags = tag_repository.get_names_for_meanings(session, meaning_ids)
    return tuple(
        _to_meaning(
            record,
            scopes,
            terms,
            tags,
        )
        for record in records
    )


def _to_meaning(
    record: Meaning,
    scopes: dict[int, Scope],
    terms: Mapping[int, tuple[str, ...]],
    tags: dict[int, tuple[str, ...]],
) -> MeaningDto:
    meaning_id = required_id(record.meaning_id)
    scope = scopes.get(record.scope_id)
    if scope is None:  # pragma: no cover - protected by the foreign key
        message = f"Meaning {meaning_id} has no scope."
        raise RuntimeError(message)
    return MeaningDto(
        meaning_id=meaning_id,
        public_id=record.public_id,
        full_name=record.full_name,
        scope_id=record.scope_id,
        scope_public_id=scope.public_id,
        scope=scope.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
        is_favorite=record.is_favorite,
        terms=terms.get(meaning_id, ()),
        tags=tags.get(meaning_id, ()),
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
        deleted_by_id=record.deleted_by_id,
    )


def to_occurrence(record: Occurrence) -> OccurrenceItem:
    return OccurrenceItem(
        occurrence_id=required_id(record.occurrence_id),
        public_id=record.public_id,
        keyword=record.keyword,
        memo=record.memo,
        source=record.source,
        status=record.status,
        occurred_at=record.occurred_at,
        updated_at=record.updated_at,
        meaning_id=record.meaning_id,
        resolved_at=record.resolved_at,
        discarded_at=record.discarded_at,
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
        resolved_by_id=record.resolved_by_id,
        discarded_by_id=record.discarded_by_id,
    )


def to_scope(record: Scope) -> ScopeDto:
    return ScopeDto(
        scope_id=required_id(record.scope_id),
        public_id=record.public_id,
        name=record.name,
        description=record.description,
        created_at=record.created_at,
        updated_at=record.updated_at,
        created_by_id=record.created_by_id,
        updated_by_id=record.updated_by_id,
    )
