"""Meaning tag management use cases."""

from termkeeper.application.errors import NotFoundError, ValidationError
from termkeeper.application.mapping import to_meaning
from termkeeper.application.support import get_meaning, user_id
from termkeeper.domain import Meaning, TagSummary
from termkeeper.infrastructure.repositories import settings_repository, tag_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class TagUseCases:
    def add_tag(self, meaning_id: int, name: str) -> Meaning:
        _validate_tag(name)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            actor_id = user_id(settings_repository.get_profile(uow.session))
            tag_repository.add(uow.session, meaning_id, name, actor_id)
            uow.session.flush()
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def remove_tag(self, meaning_id: int, name: str) -> Meaning:
        _validate_tag(name)
        with UnitOfWork() as uow:
            meaning = get_meaning(uow, meaning_id)
            if not tag_repository.remove(uow.session, meaning_id, name):
                message = f"Tag '{name}' was not found on meaning {meaning_id}."
                raise NotFoundError(message)
            result = to_meaning(uow.session, meaning)
            uow.commit()
            return result

    def tags(self) -> list[TagSummary]:
        with UnitOfWork() as uow:
            return [
                TagSummary(name=name, meaning_count=count)
                for name, count in tag_repository.list_summaries(uow.session)
            ]


def _validate_tag(name: str) -> None:
    if not name.strip():
        message = "Tag must not be empty."
        raise ValidationError(message)
