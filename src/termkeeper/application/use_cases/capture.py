"""Occurrence capture and explicit classification use cases."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning, to_occurrence
from termkeeper.application.support import (
    get_meaning,
    get_occurrence,
    get_scope_by_name,
    required_id,
    user_id,
)
from termkeeper.domain import (
    CaptureResult,
    Meaning,
    OccurrenceItem,
    OccurrenceStatus,
)
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    settings_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork

DEFAULT_SCOPE = "General"


class CaptureUseCases:
    def add(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
        *,
        meaning_id: int | None = None,
    ) -> CaptureResult:
        keyword = _required_text(keyword, "Keyword")
        memo = _optional_text(memo, "Memo")
        source = _optional_text(source, "Source")
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            if meaning_id is not None:
                get_meaning(uow, meaning_id)
            occurrence = occurrence_repository.create(
                uow.session,
                occurrence_repository.NewOccurrence(
                    keyword,
                    actor_id,
                    meaning_id=meaning_id,
                    memo=memo,
                    source=source,
                ),
            )
            candidates = (
                ()
                if meaning_id is not None
                else tuple(
                    to_meaning(uow.session, record)
                    for record in meaning_repository.find_candidates(uow.session, keyword)
                )
            )
            result = CaptureResult(to_occurrence(occurrence), candidates)
            uow.commit()
            return result

    def get_occurrence(self, occurrence_id: int) -> OccurrenceItem:
        with UnitOfWork() as uow:
            return to_occurrence(get_occurrence(uow, occurrence_id))

    def resolution_options(self, occurrence_id: int) -> CaptureResult:
        """Return a pending occurrence and all meanings matching its term."""
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            _require_status(occurrence.status, OccurrenceStatus.PENDING)
            candidates = tuple(
                to_meaning(uow.session, record)
                for record in meaning_repository.find_candidates(
                    uow.session,
                    occurrence.keyword,
                )
            )
            return CaptureResult(to_occurrence(occurrence), candidates)

    def get_occurrence_by_public_id(self, public_id: UUID) -> OccurrenceItem:
        with UnitOfWork() as uow:
            record = occurrence_repository.get_by_public_id(uow.session, public_id)
            if record is None:
                message = f"Occurrence {public_id} was not found."
                raise NotFoundError(message)
            return to_occurrence(record)

    def resolve(
        self,
        occurrence_id: int,
        full_name: str,
        description: str | None = None,
        scope: str = DEFAULT_SCOPE,
    ) -> Meaning:
        full_name = _required_text(full_name, "Full name")
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            _require_status(occurrence.status, OccurrenceStatus.PENDING)
            scope_record = get_scope_by_name(uow, scope)
            scope_id = required_id(scope_record.scope_id)
            _ensure_unique_meaning(uow, full_name, scope_id, scope_record.name)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning = meaning_repository.create(
                uow.session,
                meaning_repository.MeaningValues(
                    full_name,
                    scope_id,
                    description,
                    actor_id,
                ),
            )
            meaning_id = required_id(meaning.meaning_id)
            meaning_repository.add_term(uow.session, meaning_id, occurrence.keyword, actor_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, actor_id)
            occurrence_repository.assign(
                uow.session,
                occurrence,
                meaning_id,
                actor_id,
            )
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def assign(self, occurrence_id: int, meaning_id: int) -> OccurrenceItem:
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            if occurrence.status == OccurrenceStatus.DISCARDED:
                message = "A discarded occurrence must be reopened before assignment."
                raise ValidationError(message)
            get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            occurrence_repository.assign(uow.session, occurrence, meaning_id, actor_id)
            result = to_occurrence(occurrence)
            uow.commit()
            return result

    def unresolve(self, occurrence_id: int) -> OccurrenceItem:
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            _require_status(occurrence.status, OccurrenceStatus.RESOLVED)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            occurrence_repository.unresolve(uow.session, occurrence, actor_id)
            result = to_occurrence(occurrence)
            uow.commit()
            return result

    def discard(self, occurrence_id: int) -> OccurrenceItem:
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            _require_status(occurrence.status, OccurrenceStatus.PENDING)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            occurrence_repository.discard(uow.session, occurrence, actor_id)
            result = to_occurrence(occurrence)
            uow.commit()
            return result

    def reopen(self, occurrence_id: int) -> OccurrenceItem:
        with UnitOfWork() as uow:
            occurrence = get_occurrence(uow, occurrence_id)
            _require_status(occurrence.status, OccurrenceStatus.DISCARDED)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            occurrence_repository.unresolve(uow.session, occurrence, actor_id)
            result = to_occurrence(occurrence)
            uow.commit()
            return result


def _required_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        message = f"{label} must not be empty."
        raise ValidationError(message)
    return normalized


def _optional_text(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, label)


def _require_status(actual: OccurrenceStatus, expected: OccurrenceStatus) -> None:
    if actual != expected:
        message = f"Occurrence must be {expected.value}; current status is {actual.value}."
        raise ValidationError(message)


def _ensure_unique_meaning(
    uow: UnitOfWork,
    full_name: str,
    scope_id: int,
    scope_name: str,
) -> None:
    duplicate = meaning_repository.find_duplicate(uow.session, full_name, scope_id)
    if duplicate is not None:
        message = (
            f"Meaning '{full_name}' already exists in scope '{scope_name}' "
            f"as #{required_id(duplicate.meaning_id)}."
        )
        raise ValidationError(message)
