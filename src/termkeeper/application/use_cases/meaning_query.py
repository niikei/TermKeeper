"""Meaning read and list use cases."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.support import get_meaning, get_scope_by_name, required_id
from termkeeper.application.validation import (
    optional_filter,
    required_filter,
    to_utc,
    validate_page,
)
from termkeeper.domain import Meaning, MeaningListQuery, Page
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import meaning_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MeaningQueryUseCases:
    """Read active meanings without changing classification state."""

    def meaning_page(
        self,
        query: MeaningListQuery | None = None,
    ) -> Page[Meaning]:
        query = query or MeaningListQuery()
        validate_page(query.offset, query.limit, resource="Meaning", max_limit=100)
        tags = tuple(required_filter(tag, name="Tag") for tag in query.tags)
        if len({normalize_keyword(tag) for tag in tags}) != len(tags):
            message = "Tag filters must not contain duplicates."
            raise ValidationError(message)
        scope = optional_filter(query.scope, name="Scope")
        with UnitOfWork() as uow:
            selected_scope = get_scope_by_name(uow, scope) if scope else None
            records = meaning_repository.list_page(
                uow.session,
                scope_id=(
                    required_id(selected_scope.scope_id) if selected_scope is not None else None
                ),
                favorite_only=query.favorite_only,
                tags=tags,
                tag_match=query.tag_match,
                created_since=to_utc(query.created_since),
                updated_since=to_utc(query.updated_since),
                has_description=query.has_description,
                has_alias=query.has_alias,
                sort=query.sort,
                order=query.order,
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


def _filter_tag(meanings: list[Meaning], tag: str | None) -> list[Meaning]:
    if not tag:
        return meanings
    tag_norm = normalize_keyword(tag)
    return [
        meaning
        for meaning in meanings
        if any(normalize_keyword(name) == tag_norm for name in meaning.tags)
    ]
