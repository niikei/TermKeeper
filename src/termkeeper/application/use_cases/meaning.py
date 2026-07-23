"""Meaning and alias management use cases."""

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
from termkeeper.application.validation import optional_filter, validate_page
from termkeeper.domain import Meaning, MeaningListQuery, Page, PageQuery
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    settings_repository,
)
from termkeeper.infrastructure.tables import Meaning as MeaningRecord
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MeaningUseCases:
    def meaning_page(
        self,
        query: MeaningListQuery | None = None,
    ) -> Page[Meaning]:
        query = query or MeaningListQuery()
        validate_page(
            query.offset,
            query.limit,
            resource="Meaning",
            max_limit=100,
        )
        tag = optional_filter(query.tag, name="Tag")
        scope = optional_filter(query.scope, name="Scope")
        with UnitOfWork() as uow:
            selected_scope = get_scope_by_name(uow, scope) if scope else None
            records = meaning_repository.list_page(
                uow.session,
                scope_id=(
                    required_id(selected_scope.scope_id) if selected_scope is not None else None
                ),
                favorite_only=query.favorite_only,
                tag=tag,
                offset=query.offset,
                limit=query.limit,
            )
            return Page(
                items=tuple(to_meaning(uow.session, record) for record in records[: query.limit]),
                offset=query.offset,
                limit=query.limit,
                has_more=len(records) > query.limit,
            )

    def get_meaning(self, meaning_id: int) -> Meaning:
        with UnitOfWork() as uow:
            return to_meaning(uow.session, get_meaning(uow, meaning_id))

    def get_meaning_by_public_id(
        self,
        public_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Meaning:
        with UnitOfWork() as uow:
            record = meaning_repository.get_by_public_id(
                uow.session,
                public_id,
                include_deleted=include_deleted,
            )
            if record is None:
                message = f"Meaning {public_id} was not found."
                raise NotFoundError(message)
            return to_meaning(uow.session, record)

    def meaning_public_ids(self, meaning_ids: set[int]) -> dict[int, UUID]:
        with UnitOfWork() as uow:
            return meaning_repository.get_public_ids(uow.session, meaning_ids)

    def create_meaning(
        self,
        full_name: str,
        description: str | None = None,
        terms: tuple[str, ...] = (),
        scope: str = "General",
        public_id: UUID | None = None,
    ) -> Meaning:
        _validate_name(full_name)
        with UnitOfWork() as uow:
            scope_record = get_scope_by_name(uow, scope)
            scope_id = required_id(scope_record.scope_id)
            _ensure_unique(uow, full_name, scope_id, scope_record.name)
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

    def meanings(
        self,
        tag: str | None = None,
        *,
        scope: str | None = None,
        favorite_only: bool = False,
    ) -> list[Meaning]:
        with UnitOfWork() as uow:
            selected_scope = get_scope_by_name(uow, scope) if scope else None
            meanings = [
                to_meaning(uow.session, row)
                for row in meaning_repository.list_all(
                    uow.session,
                    scope_id=(
                        required_id(selected_scope.scope_id) if selected_scope is not None else None
                    ),
                    favorite_only=favorite_only,
                )
            ]
            return _filter_tag(meanings, tag)

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
        _validate_name(full_name)
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
            _ensure_unique(
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
            _ensure_unique(
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


def _validate_name(full_name: str) -> None:
    if not full_name.strip():
        message = "Full name must not be empty."
        raise ValidationError(message)


def _ensure_unique(
    uow: UnitOfWork,
    full_name: str,
    scope_id: int,
    scope_name: str,
    *,
    exclude_id: int | None = None,
) -> None:
    duplicate = meaning_repository.find_duplicate(
        uow.session,
        full_name,
        scope_id,
        exclude_id=exclude_id,
    )
    if duplicate is not None:
        message = f"Meaning '{full_name}' already exists in scope '{scope_name}'."
        raise ValidationError(message)


def _get_deleted_meaning(uow: UnitOfWork, meaning_id: int) -> MeaningRecord:
    meaning = meaning_repository.get(uow.session, meaning_id, include_deleted=True)
    if meaning is None or meaning.deleted_at is None:
        message = f"Deleted meaning {meaning_id} was not found."
        raise NotFoundError(message)
    return meaning


def _filter_tag(meanings: list[Meaning], tag: str | None) -> list[Meaning]:
    if not tag:
        return meanings
    tag_norm = normalize_keyword(tag)
    return [
        meaning
        for meaning in meanings
        if any(normalize_keyword(name) == tag_norm for name in meaning.tags)
    ]
