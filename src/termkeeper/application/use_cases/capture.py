"""Single and atomic batch occurrence capture use cases."""

from collections.abc import Sequence

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meanings, to_occurrence
from termkeeper.application.support import required_id, user_id
from termkeeper.domain import (
    CaptureBatchResult,
    CaptureInput,
    CaptureResult,
)
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    settings_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork

MAX_CAPTURE_BATCH_SIZE = 100


class CaptureUseCases:
    def add(
        self,
        keyword: str,
        memo: str | None = None,
        source: str | None = None,
        *,
        meaning_id: int | None = None,
    ) -> CaptureResult:
        return self.capture_many(
            (CaptureInput(keyword, memo, source, meaning_id),),
        ).items[0]

    def capture_many(
        self,
        items: Sequence[CaptureInput],
    ) -> CaptureBatchResult:
        normalized = _normalize_capture_batch(items)
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            _validate_meaning_ids(uow, normalized)
            candidates_by_keyword = meaning_repository.find_candidates_for_keywords(
                uow.session,
                {item.keyword for item in normalized if item.meaning_id is None},
            )
            candidate_records = {
                required_id(record.meaning_id): record
                for records in candidates_by_keyword.values()
                for record in records
            }
            candidate_meanings = {
                meaning.meaning_id: meaning
                for meaning in to_meanings(
                    uow.session,
                    tuple(candidate_records.values()),
                )
            }
            occurrences = occurrence_repository.create_many(
                uow.session,
                tuple(
                    occurrence_repository.NewOccurrence(
                        item.keyword,
                        actor_id,
                        meaning_id=item.meaning_id,
                        memo=item.memo,
                        source=item.source,
                    )
                    for item in normalized
                ),
            )
            results = tuple(
                CaptureResult(
                    to_occurrence(occurrence),
                    tuple(
                        candidate_meanings[required_id(record.meaning_id)]
                        for record in candidates_by_keyword.get(
                            normalize_keyword(item.keyword),
                            (),
                        )
                    ),
                )
                for item, occurrence in zip(normalized, occurrences, strict=True)
            )
            uow.commit()
            return CaptureBatchResult(results)


def _validate_meaning_ids(
    uow: UnitOfWork,
    items: tuple[CaptureInput, ...],
) -> None:
    meaning_ids = {item.meaning_id for item in items if item.meaning_id is not None}
    existing = meaning_repository.get_many(uow.session, meaning_ids)
    for item in items:
        if item.meaning_id is not None and item.meaning_id not in existing:
            message = f"Meaning {item.meaning_id} was not found."
            raise NotFoundError(message)


def _normalize_capture_batch(items: Sequence[CaptureInput]) -> tuple[CaptureInput, ...]:
    if not items:
        message = "At least one term is required."
        raise ValidationError(message)
    if len(items) > MAX_CAPTURE_BATCH_SIZE:
        message = f"A capture batch cannot exceed {MAX_CAPTURE_BATCH_SIZE} terms."
        raise ValidationError(message)
    multiple = len(items) > 1
    normalized = tuple(
        CaptureInput(
            _required_text(item.keyword, _input_label("Keyword", position, multiple=multiple)),
            _optional_text(item.memo, _input_label("Memo", position, multiple=multiple)),
            _optional_text(item.source, _input_label("Source", position, multiple=multiple)),
            item.meaning_id,
        )
        for position, item in enumerate(items, start=1)
    )
    seen: dict[str, int] = {}
    for position, item in enumerate(normalized, start=1):
        key = normalize_keyword(item.keyword)
        duplicate_position = seen.get(key)
        if duplicate_position is not None:
            message = (
                f"Keyword at position {position} duplicates position "
                f"{duplicate_position}: '{item.keyword}'."
            )
            raise ValidationError(message)
        seen[key] = position
    return normalized


def _input_label(label: str, position: int, *, multiple: bool) -> str:
    return f"{label} at position {position}" if multiple else label


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
