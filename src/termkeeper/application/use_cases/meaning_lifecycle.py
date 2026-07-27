"""Meaning trash, restore, and purge use cases."""

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.support import get_meaning, get_scope, user_id
from termkeeper.application.use_cases.meaning_support import ensure_unique_meaning
from termkeeper.application.validation import validate_page
from termkeeper.domain import Meaning, Page, PageQuery
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    settings_repository,
)
from termkeeper.infrastructure.tables import Meaning as MeaningRecord
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MeaningLifecycleUseCases:
    """Move Meaning records through the reversible deletion lifecycle."""

    def delete_meaning(self, meaning_id: int) -> None:
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.soft_delete(uow.session, meaning, actor_id)
            uow.commit()

    def trash(self) -> list[Meaning]:
        with UnitOfWork() as uow:
            return [
                to_meaning(uow.session, row) for row in meaning_repository.list_deleted(uow.session)
            ]

    def trash_page(self, query: PageQuery | None = None) -> Page[Meaning]:
        query = query or PageQuery()
        validate_page(query.offset, query.limit, resource="Trash", max_limit=100)
        with UnitOfWork() as uow:
            records = meaning_repository.list_deleted_page(
                uow.session,
                offset=query.offset,
                limit=query.limit,
            )
            return Page(
                items=tuple(to_meaning(uow.session, record) for record in records[: query.limit]),
                offset=query.offset,
                limit=query.limit,
                has_more=len(records) > query.limit,
            )

    def restore_meaning(self, meaning_id: int) -> Meaning:
        with UnitOfWork() as uow:
            meaning = _get_deleted_meaning(uow, meaning_id)
            ensure_unique_meaning(
                uow,
                meaning.full_name,
                meaning.scope_id,
                get_scope(uow, meaning.scope_id).name,
                exclude_id=meaning_id,
            )
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.restore(uow.session, meaning, actor_id)
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def purge_meaning(self, meaning_id: int) -> None:
        with UnitOfWork() as uow:
            meaning = _get_deleted_meaning(uow, meaning_id)
            references = occurrence_repository.count_meaning_references(uow.session, meaning_id)
            if references:
                message = (
                    f"Meaning {meaning_id} is referenced by {references} occurrence(s) "
                    "and cannot be purged."
                )
                raise ValidationError(message)
            meaning_repository.purge(uow.session, meaning)
            uow.commit()


def _get_deleted_meaning(uow: UnitOfWork, meaning_id: int) -> MeaningRecord:
    meaning = meaning_repository.get(uow.session, meaning_id, include_deleted=True)
    if meaning is None or meaning.deleted_at is None:
        message = f"Deleted meaning {meaning_id} was not found."
        raise NotFoundError(message)
    return meaning
