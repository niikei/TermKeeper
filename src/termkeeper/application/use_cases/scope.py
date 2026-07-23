"""Meaning scope management use cases."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_scope
from termkeeper.application.support import get_scope, user_id
from termkeeper.domain import Scope
from termkeeper.infrastructure.repositories import scope_repository, settings_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork

GENERAL_SCOPE_ID = 1


class ScopeUseCases:
    def create_scope(self, name: str, description: str | None = None) -> Scope:
        _validate_name(name)
        with UnitOfWork() as uow:
            _ensure_unique(uow, name)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            record = scope_repository.create(
                uow.session,
                scope_repository.ScopeValues(name, description, actor_id),
            )
            result = to_scope(record)
            uow.commit()
            return result

    def get_scope(self, scope_id: int) -> Scope:
        with UnitOfWork() as uow:
            return to_scope(get_scope(uow, scope_id))

    def scopes(self) -> list[Scope]:
        with UnitOfWork() as uow:
            return [to_scope(record) for record in scope_repository.list_all(uow.session)]

    def get_scope_by_public_id(self, public_id: UUID) -> Scope:
        with UnitOfWork() as uow:
            record = scope_repository.get_by_public_id(uow.session, public_id)
            if record is None:
                message = f"Scope {public_id} was not found."
                raise NotFoundError(message)
            return to_scope(record)

    def edit_scope(
        self,
        scope_id: int,
        name: str,
        description: str | None,
    ) -> Scope:
        _validate_name(name)
        with UnitOfWork() as uow:
            record = get_scope(uow, scope_id)
            _ensure_unique(uow, name, exclude_id=scope_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            scope_repository.update(
                uow.session,
                record,
                scope_repository.ScopeValues(name, description, actor_id),
            )
            result = to_scope(record)
            uow.commit()
            return result

    def delete_scope(self, scope_id: int) -> None:
        with UnitOfWork() as uow:
            record = get_scope(uow, scope_id)
            if scope_id == GENERAL_SCOPE_ID:
                message = "The General scope cannot be deleted."
                raise ValidationError(message)
            references = scope_repository.count_meanings(uow.session, scope_id)
            if references:
                message = f"Scope {scope_id} is used by {references} meaning(s)."
                raise ValidationError(message)
            scope_repository.remove(uow.session, record)
            uow.commit()


def _validate_name(name: str) -> None:
    if not name.strip():
        message = "Scope name must not be empty."
        raise ValidationError(message)


def _ensure_unique(
    uow: UnitOfWork,
    name: str,
    *,
    exclude_id: int | None = None,
) -> None:
    existing = scope_repository.get_by_name(uow.session, name)
    if existing is None or existing.scope_id == exclude_id:
        return
    message = f"Scope '{name}' already exists."
    raise ValidationError(message)
