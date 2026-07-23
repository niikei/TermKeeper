"""Meaning creation, editing, aliases, and favorites."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.support import (
    get_meaning,
    get_scope,
    get_scope_by_name,
    required_id,
    user_id,
)
from termkeeper.application.use_cases.meaning_support import (
    ensure_unique_meaning,
    validate_meaning_name,
)
from termkeeper.domain import Meaning
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import meaning_repository, settings_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MeaningCommandUseCases:
    """Create and update active Meaning data."""

    def create_meaning(
        self,
        full_name: str,
        description: str | None = None,
        terms: tuple[str, ...] = (),
        scope: str = "General",
        public_id: UUID | None = None,
    ) -> Meaning:
        validate_meaning_name(full_name)
        for term in terms:
            if not term.strip():
                message = "Meaning aliases must not be empty."
                raise ValidationError(message)
        with UnitOfWork() as uow:
            scope_record = get_scope_by_name(uow, scope)
            scope_id = required_id(scope_record.scope_id)
            ensure_unique_meaning(uow, full_name, scope_id, scope_record.name)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            record = meaning_repository.create(
                uow.session,
                meaning_repository.MeaningValues(
                    full_name,
                    scope_id,
                    description,
                    actor_id,
                ),
                public_id=public_id,
            )
            meaning_id = required_id(record.meaning_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, actor_id)
            for term in terms:
                meaning_repository.add_term(uow.session, meaning_id, term, actor_id)
            uow.session.flush()
            result = to_meaning(uow.session, record)
            uow.commit()
            return result

    def favorite_meaning(self, meaning_id: int) -> Meaning:
        return self._set_favorite(meaning_id, favorite=True)

    def unfavorite_meaning(self, meaning_id: int) -> Meaning:
        return self._set_favorite(meaning_id, favorite=False)

    def _set_favorite(self, meaning_id: int, *, favorite: bool) -> Meaning:
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.set_favorite(
                uow.session,
                meaning,
                actor_id,
                favorite=favorite,
            )
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def add_alias(self, meaning_id: int, keyword: str) -> Meaning:
        if not keyword.strip():
            message = "Alias must not be empty."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.add_term(uow.session, meaning_id, keyword, actor_id)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def remove_alias(self, meaning_id: int, keyword: str) -> Meaning:
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            if normalize_keyword(keyword) == meaning.full_name_norm:
                message = "The canonical full name cannot be removed as an alias."
                raise ValidationError(message)
            if not meaning_repository.remove_term(uow.session, meaning_id, keyword):
                message = f"Alias '{keyword}' was not found."
                raise NotFoundError(message)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def edit(
        self,
        meaning_id: int,
        full_name: str,
        description: str | None,
        scope: str | None = None,
    ) -> Meaning:
        validate_meaning_name(full_name)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            selected_scope = get_scope_by_name(uow, scope) if scope is not None else None
            scope_id = (
                required_id(selected_scope.scope_id)
                if selected_scope is not None
                else meaning.scope_id
            )
            scope_name = (
                selected_scope.name
                if selected_scope is not None
                else get_scope(uow, meaning.scope_id).name
            )
            ensure_unique_meaning(
                uow,
                full_name,
                scope_id,
                scope_name,
                exclude_id=meaning_id,
            )
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.update(
                uow.session,
                meaning,
                meaning_repository.MeaningValues(
                    full_name,
                    scope_id,
                    description,
                    actor_id,
                ),
            )
            meaning_repository.add_term(uow.session, meaning_id, full_name, actor_id)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result
