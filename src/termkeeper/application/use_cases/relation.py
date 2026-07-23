"""Meaning relationship use cases."""

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.support import get_meaning, user_id
from termkeeper.domain import Meaning
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    relation_repository,
    settings_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class RelationUseCases:
    def related(self, meaning_id: int) -> list[Meaning]:
        with UnitOfWork() as uow:
            get_meaning(uow, meaning_id)
            return [
                to_meaning(uow.session, record)
                for record in relation_repository.list_related(uow.session, meaning_id)
            ]

    def relate(self, meaning_id: int, related_id: int) -> list[Meaning]:
        _validate_pair(meaning_id, related_id)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            related = get_meaning(uow, related_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            if relation_repository.add(uow.session, meaning_id, related_id, actor_id):
                meaning_repository.touch(uow.session, meaning, actor_id)
                meaning_repository.touch(uow.session, related, actor_id)
            result = [
                to_meaning(uow.session, record)
                for record in relation_repository.list_related(uow.session, meaning_id)
            ]
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
            result = [
                to_meaning(uow.session, record)
                for record in relation_repository.list_related(uow.session, meaning_id)
            ]
            uow.commit()
            return result


def _validate_pair(meaning_id: int, related_id: int) -> None:
    if meaning_id == related_id:
        message = "A meaning cannot be related to itself."
        raise ValidationError(message)
