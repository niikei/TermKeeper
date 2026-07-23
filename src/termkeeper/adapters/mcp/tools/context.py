"""Shared MCP tool dependencies and identifier resolution."""

from uuid import UUID

from termkeeper.adapters.external import ExternalMapper
from termkeeper.application import TermKeeperService


class ToolContext:
    def __init__(self, service: TermKeeperService) -> None:
        self._service = service
        self._mapper = ExternalMapper(service)

    def _local_meaning_id(
        self,
        public_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> int:
        return self._service.get_meaning_by_public_id(
            public_id,
            include_deleted=include_deleted,
        ).meaning_id

    def _local_occurrence_id(self, public_id: UUID) -> int:
        return self._service.get_occurrence_by_public_id(public_id).occurrence_id
