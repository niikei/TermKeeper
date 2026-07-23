"""Single and atomic batch occurrence capture use cases."""

from collections.abc import Sequence

from termkeeper.application.errors import ValidationError
from termkeeper.application.mapping import to_meaning, to_occurrence
from termkeeper.application.support import (
    get_meaning,
    user_id,
)
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
            for item in normalized:
                if item.meaning_id is not None:
                    get_meaning(uow, item.meaning_id)
            results = tuple(_capture(uow, item, actor_id) for item in normalized)
            uow.commit()
            return CaptureBatchResult(results)


def _capture(
    uow: UnitOfWork,
    item: CaptureInput,
    actor_id: int | None,
) -> CaptureResult:
    occurrence = occurrence_repository.create(
        uow.session,
        occurrence_repository.NewOccurrence(
            item.keyword,
            actor_id,
            meaning_id=item.meaning_id,
            memo=item.memo,
            source=item.source,
        ),
    )
    candidates = (
        ()
        if item.meaning_id is not None
        else tuple(
            to_meaning(uow.session, record)
            for record in meaning_repository.find_candidates(
                uow.session,
                item.keyword,
            )
        )
    )
    return CaptureResult(to_occurrence(occurrence), candidates)


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
