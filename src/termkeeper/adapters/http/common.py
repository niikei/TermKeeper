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


def _local_occurrence_id(service: TermKeeperService, public_id: UUID) -> int:
    return service.get_occurrence_by_public_id(public_id).occurrence_id


def _scope_name(service: TermKeeperService, public_id: UUID) -> str:
    return service.get_scope_by_public_id(public_id).name
