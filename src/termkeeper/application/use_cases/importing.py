"""Atomic batch import use case."""

from uuid import UUID

from termkeeper.application.errors import ValidationError
from termkeeper.application.support import required_id, user_id
from termkeeper.domain import ImportIssue, ImportResult, ImportRow
from termkeeper.infrastructure import meaning_repository, settings_repository, tag_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class ImportUseCases:
    def import_meanings(
        self,
        rows: tuple[ImportRow, ...],
        *,
        dry_run: bool = False,
        strict: bool = False,
    ) -> ImportResult:
        valid_rows, issues = _validate_rows(rows)
        if strict and issues:
            message = "; ".join(f"row {issue.row_number}: {issue.message}" for issue in issues)
            raise ValidationError(message)
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            created = updated = 0
            for row, public_id in valid_rows:
                existing = (
                    meaning_repository.get_by_public_id(uow.session, public_id)
                    if public_id is not None
                    else None
                )
                if existing is None:
                    created += 1
                    if not dry_run:
                        _create(uow, row, public_id, actor_id)
                else:
                    updated += 1
                    if not dry_run:
                        _update(uow, row, required_id(existing.meaning_id), actor_id)
            if not dry_run:
                uow.commit()
            return ImportResult(
                created=created,
                updated=updated,
                skipped=len(issues),
                dry_run=dry_run,
                issues=issues,
            )


def _validate_rows(
    rows: tuple[ImportRow, ...],
) -> tuple[list[tuple[ImportRow, UUID | None]], tuple[ImportIssue, ...]]:
    valid: list[tuple[ImportRow, UUID | None]] = []
    issues: list[ImportIssue] = []
    seen_ids: set[UUID] = set()
    for row in rows:
        if not row.full_name.strip():
            issues.append(ImportIssue(row.row_number, "full_name must not be empty"))
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
        valid.append((row, public_id))
    return valid, tuple(issues)


def _create(
    uow: UnitOfWork,
    row: ImportRow,
    public_id: UUID | None,
    actor_id: int | None,
) -> None:
    record = meaning_repository.create(
        uow.session,
        row.full_name,
        row.description,
        actor_id,
        public_id=public_id,
    )
    meaning_id = required_id(record.meaning_id)
    _add_metadata(uow, meaning_id, row, actor_id)


def _update(
    uow: UnitOfWork,
    row: ImportRow,
    meaning_id: int,
    actor_id: int | None,
) -> None:
    record = meaning_repository.get(uow.session, meaning_id)
    if record is None:
        message = f"Meaning {meaning_id} disappeared during import."
        raise RuntimeError(message)
    meaning_repository.update(uow.session, record, row.full_name, row.description, actor_id)
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
