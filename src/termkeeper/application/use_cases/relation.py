"""Meaning relationship use cases."""

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meanings
from termkeeper.application.support import get_meaning, user_id
from termkeeper.application.validation import validate_page
from termkeeper.domain import Meaning, Page, PageQuery
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    relation_repository,
    settings_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class RelationUseCases:
    def related_page(
        self,
        meaning_id: int,
        query: PageQuery | None = None,
    ) -> Page[Meaning]:
        query = query or PageQuery()
        validate_page(query.offset, query.limit, resource="Relation", max_limit=100)
        with UnitOfWork() as uow:
            get_meaning(uow, meaning_id)
            records = relation_repository.list_related_page(
                uow.session,
                meaning_id,
                offset=query.offset,
                limit=query.limit,
            )
            return Page(
                items=to_meanings(uow.session, records[: query.limit]),
                offset=query.offset,
                limit=query.limit,
                has_more=len(records) > query.limit,
            )

    def related(self, meaning_id: int) -> list[Meaning]:
        with UnitOfWork() as uow:
            get_meaning(uow, meaning_id)
            return list(
                to_meanings(
                    uow.session,
                    relation_repository.list_related(uow.session, meaning_id),
                ),
            )

    def relate(self, meaning_id: int, related_id: int) -> list[Meaning]:
        _validate_pair(meaning_id, related_id)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            related = get_meaning(uow, related_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            if relation_repository.add(uow.session, meaning_id, related_id, actor_id):
                meaning_repository.touch(uow.session, meaning, actor_id)
                meaning_repository.touch(uow.session, related, actor_id)
            result = list(
                to_meanings(
                    uow.session,
                    relation_repository.list_related(uow.session, meaning_id),
                ),
            )
            uow.commit()
            return result

    def unrelate(self, meaning_id: int, related_id: int) -> list[Meaning]:
        _validate_pair(meaning_id, related_id)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            related = get_meaning(uow, related_id)
            if not relation_repository.remove(uow.session, meaning_id, related_id):
                message = f"Meanings {meaning_id} and {related_id} are not related."
                raise NotFoundError(message)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            meaning_repository.touch(uow.session, meaning, actor_id)
            meaning_repository.touch(uow.session, related, actor_id)
            uow.session.flush()
            result = list(
                to_meanings(
                    uow.session,
                    relation_repository.list_related(uow.session, meaning_id),
                ),
            )
            uow.commit()
            return result


def _validate_pair(meaning_id: int, related_id: int) -> None:
    if meaning_id == related_id:
        message = "A meaning cannot be related to itself."
        raise ValidationError(message)
