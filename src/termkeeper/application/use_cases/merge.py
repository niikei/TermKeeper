"""Meaning merge use case."""

from termkeeper.application.errors import ValidationError
from termkeeper.application.support import get_meaning, user_id
from termkeeper.domain import MergeResult
from termkeeper.infrastructure.repositories import (
    inbox_repository,
    meaning_repository,
    settings_repository,
    tag_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class MergeUseCases:
    def merge_meanings(
        self,
        source_id: int,
        target_id: int,
        *,
        dry_run: bool = False,
    ) -> MergeResult:
        if source_id == target_id:
            message = "Source and target meanings must be different."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            source = get_meaning(uow, source_id)
            target = get_meaning(uow, target_id)
            terms_moved = meaning_repository.count_terms_to_move(
                uow.session,
                source_id,
                target_id,
            )
            tags_moved = tag_repository.count_to_move(uow.session, source_id, target_id)
            occurrences_moved, inboxes_moved = inbox_repository.count_meaning_references(
                uow.session,
                source_id,
            )
            if not dry_run:
                meaning_repository.move_terms(uow.session, source_id, target_id)
                tag_repository.move(uow.session, source_id, target_id)
                inbox_repository.move_meaning_references(uow.session, source_id, target_id)
                actor_id = user_id(settings_repository.get_profile(uow.session))
                meaning_repository.touch(uow.session, target, actor_id)
                meaning_repository.purge(uow.session, source)
                uow.commit()
            return MergeResult(
                source_meaning_id=source_id,
                target_meaning_id=target_id,
                terms_moved=terms_moved,
                tags_moved=tags_moved,
                occurrences_moved=occurrences_moved,
                inboxes_moved=inboxes_moved,
                applied=not dry_run,
            )
