"""Atomic batch import use case."""

from uuid import UUID

from termkeeper.application.errors import ValidationError
from termkeeper.application.support import required_id, user_id
from termkeeper.domain import ImportIssue, ImportResult, ImportRow
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    scope_repository,
    settings_repository,
    tag_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork

type PlannedRow = tuple[ImportRow, UUID | None, int | None, int]


class ImportUseCases:
    def import_meanings(
        self,
        rows: tuple[ImportRow, ...],
        *,
        dry_run: bool = False,
        strict: bool = False,
    ) -> ImportResult:
        valid_rows, issues = _validate_rows(rows)
        _raise_if_strict(issues, strict=strict)
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            planned, all_issues = _plan_rows(uow, valid_rows, issues)
            _raise_if_strict(all_issues, strict=strict)
            created, updated = _apply_rows(
                uow,
                planned,
                actor_id,
                dry_run=dry_run,
            )
            if not dry_run:
                uow.commit()
            return ImportResult(
                created=created,
                updated=updated,
                skipped=len(all_issues),
                dry_run=dry_run,
                issues=tuple(all_issues),
            )


def _plan_rows(
    uow: UnitOfWork,
    valid_rows: list[tuple[ImportRow, UUID | None]],
    initial_issues: tuple[ImportIssue, ...],
) -> tuple[list[PlannedRow], list[ImportIssue]]:
    planned: list[PlannedRow] = []
    issues = list(initial_issues)
    for row, public_id in valid_rows:
        scope = scope_repository.get_by_name(uow.session, row.scope)
        if scope is None:
            issues.append(
                ImportIssue(
                    row.row_number,
                    f"scope '{row.scope}' was not found",
                ),
            )
            continue
        scope_id = required_id(scope.scope_id)
        existing = (
            meaning_repository.get_by_public_id(
                uow.session,
                public_id,
                include_deleted=True,
            )
            if public_id is not None
            else None
        )
        if existing is not None and existing.deleted_at is not None:
            issues.append(
                ImportIssue(
                    row.row_number,
                    "public_id belongs to a deleted meaning; restore it before import",
                ),
            )
            continue
        meaning_id = required_id(existing.meaning_id) if existing is not None else None
        duplicate = meaning_repository.find_duplicate(
            uow.session,
            row.full_name,
            scope_id,
            exclude_id=meaning_id,
        )
        if duplicate is not None:
            issues.append(
                ImportIssue(
                    row.row_number,
                    "full_name already exists in the same scope",
                ),
            )
            continue
        planned.append((row, public_id, meaning_id, scope_id))
    return planned, issues


def _apply_rows(
    uow: UnitOfWork,
    planned: list[PlannedRow],
    actor_id: int | None,
    *,
    dry_run: bool,
) -> tuple[int, int]:
    created = updated = 0
    for row, public_id, meaning_id, scope_id in planned:
        if meaning_id is None:
            created += 1
            if not dry_run:
                _create(uow, row, public_id, scope_id, actor_id)
        else:
            updated += 1
            if not dry_run:
                _update(uow, row, meaning_id, scope_id, actor_id)
    return created, updated


def _raise_if_strict(issues: tuple[ImportIssue, ...] | list[ImportIssue], *, strict: bool) -> None:
    if strict and issues:
        message = "; ".join(f"row {issue.row_number}: {issue.message}" for issue in issues)
        raise ValidationError(message)


def _validate_rows(
    rows: tuple[ImportRow, ...],
) -> tuple[list[tuple[ImportRow, UUID | None]], tuple[ImportIssue, ...]]:
    valid: list[tuple[ImportRow, UUID | None]] = []
    issues: list[ImportIssue] = []
    seen_ids: set[UUID] = set()
    seen_meanings: set[tuple[str, str]] = set()
    for row in rows:
        if not row.full_name.strip():
            issues.append(ImportIssue(row.row_number, "full_name must not be empty"))
            continue
        if not row.scope.strip():
            issues.append(ImportIssue(row.row_number, "scope must not be empty"))
            continue
        meaning_key = (
            normalize_keyword(row.scope),
            normalize_keyword(row.full_name),
        )
        if meaning_key in seen_meanings:
            issues.append(
                ImportIssue(
                    row.row_number,
                    "full_name is duplicated in the same scope in the file",
                ),
            )
            continue
        try:
            public_id = UUID(row.public_id) if row.public_id else None
        except ValueError:
            issues.append(ImportIssue(row.row_number, "public_id must be a valid UUID"))
            continue
        if public_id is not None and public_id in seen_ids:
            issues.append(ImportIssue(row.row_number, "public_id is duplicated in the file"))
            continue
        if public_id is not None:
            seen_ids.add(public_id)
        seen_meanings.add(meaning_key)
        valid.append((row, public_id))
    return valid, tuple(issues)


def _create(
    uow: UnitOfWork,
    row: ImportRow,
    public_id: UUID | None,
    scope_id: int,
    actor_id: int | None,
) -> None:
    record = meaning_repository.create(
        uow.session,
        meaning_repository.MeaningValues(
            row.full_name,
            scope_id,
            row.description,
            actor_id,
        ),
        public_id=public_id,
    )
    meaning_id = required_id(record.meaning_id)
    _add_metadata(uow, meaning_id, row, actor_id)


def _update(
    uow: UnitOfWork,
    row: ImportRow,
    meaning_id: int,
    scope_id: int,
    actor_id: int | None,
) -> None:
    record = meaning_repository.get(uow.session, meaning_id)
    if record is None:  # pragma: no cover - cannot change within this unit of work
        message = f"Meaning {meaning_id} disappeared during import."
        raise RuntimeError(message)
    meaning_repository.update(
        uow.session,
        record,
        meaning_repository.MeaningValues(
            row.full_name,
            scope_id,
            row.description,
            actor_id,
        ),
    )
    _add_metadata(uow, meaning_id, row, actor_id)


def _add_metadata(
    uow: UnitOfWork,
    meaning_id: int,
    row: ImportRow,
    actor_id: int | None,
) -> None:
    meaning_repository.add_term(uow.session, meaning_id, row.full_name, actor_id)
    for term in row.terms:
        meaning_repository.add_term(uow.session, meaning_id, term, actor_id)
    for tag in row.tags:
        tag_repository.add(uow.session, meaning_id, tag, actor_id)
