"""Shared HTTP identifier resolution."""

from uuid import UUID

from termkeeper.application import TermKeeperService


def _local_meaning_id(
    service: TermKeeperService,
    public_id: UUID,
    *,
    include_deleted: bool = False,
) -> int:
    return service.get_meaning_by_public_id(
        public_id,
        include_deleted=include_deleted,
    ).meaning_id


def _local_inbox_id(service: TermKeeperService, public_id: UUID) -> int:
    return service.get_inbox_by_public_id(public_id).inbox_id
