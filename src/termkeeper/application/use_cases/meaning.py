"""Meaning and alias management use cases."""

from uuid import UUID

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.search import rank_search, search_tokens
from termkeeper.application.support import get_meaning, required_id, user_id
from termkeeper.domain import Meaning, SearchHit, SearchQuery
from termkeeper.infrastructure import meaning_repository, settings_repository
from termkeeper.infrastructure.sqlite_utils import normalize_keyword
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MeaningUseCases:
    def get_meaning(self, meaning_id: int) -> Meaning:
        with UnitOfWork() as uow:
            return to_meaning(uow.session, get_meaning(uow, meaning_id))

    def get_meaning_by_public_id(self, public_id: UUID) -> Meaning:
        with UnitOfWork() as uow:
            record = meaning_repository.get_by_public_id(uow.session, public_id)
            if record is None:
                message = f"Meaning {public_id} was not found."
                raise NotFoundError(message)
            return to_meaning(uow.session, record)

    def create_meaning(
        self,
        full_name: str,
        description: str | None = None,
        terms: tuple[str, ...] = (),
        public_id: UUID | None = None,
    ) -> Meaning:
        _validate_name(full_name)
        with UnitOfWork() as uow:
            actor_id = user_id(settings_repository.get_profile(uow.session))
            record = meaning_repository.create(
                uow.session,
                full_name,
                description,
                actor_id,
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

    def search(
        self,
        query: SearchQuery | str,
    ) -> list[SearchHit]:
        query = SearchQuery(query) if isinstance(query, str) else query
        tokens = search_tokens(query.text)
        if not tokens:
            message = "Search keyword must not be empty."
            raise ValidationError(message)
        if not 1 <= query.limit <= 100:
            message = "Search limit must be between 1 and 100."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            records = meaning_repository.search(uow.session, tokens, query.field)
            meanings = [to_meaning(uow.session, row) for row in records]
            if query.tag:
                tag_norm = normalize_keyword(query.tag)
                meanings = [
                    meaning
                    for meaning in meanings
                    if any(normalize_keyword(tag) == tag_norm for tag in meaning.tags)
                ]
            return rank_search(meanings, query)

    def meanings(self, tag: str | None = None) -> list[Meaning]:
        with UnitOfWork() as uow:
            meanings = [
                to_meaning(uow.session, row) for row in meaning_repository.list_all(uow.session)
            ]
            if not tag:
                return meanings
            tag_norm = normalize_keyword(tag)
            return [
                meaning
                for meaning in meanings
                if any(normalize_keyword(name) == tag_norm for name in meaning.tags)
            ]

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

    def edit(self, meaning_id: int, full_name: str, description: str | None) -> Meaning:
        _validate_name(full_name)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.update(uow.session, meaning, full_name, description, actor_id)
            meaning_repository.add_term(uow.session, meaning_id, full_name, actor_id)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def delete_meaning(self, meaning_id: int) -> None:
        with UnitOfWork() as uow:
            meaning_repository.delete(uow.session, get_meaning(uow, meaning_id))
            uow.commit()


def _validate_name(full_name: str) -> None:
    if not full_name.strip():
        message = "Full name must not be empty."
        raise ValidationError(message)
