"""Shared external search-query mapping for HTTP and MCP adapters."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    OccurrenceQuery,
    OccurrenceStatus,
    ScopeSearchQuery,
    SearchField,
    SearchQuery,
)


class MeaningSearchInput(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def field(self) -> str: ...

    @property
    def tag(self) -> str | None: ...

    @property
    def scope_id(self) -> UUID | None: ...

    @property
    def favorite_only(self) -> bool: ...

    @property
    def offset(self) -> int: ...

    @property
    def limit(self) -> int: ...


class OccurrenceSearchInput(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def meaning_id(self) -> UUID | None: ...

    @property
    def status(self) -> str | None: ...

    @property
    def source(self) -> str | None: ...

    @property
    def since(self) -> datetime | None: ...

    @property
    def offset(self) -> int: ...

    @property
    def limit(self) -> int: ...


class InboxSearchInput(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def source(self) -> str | None: ...

    @property
    def since(self) -> datetime | None: ...

    @property
    def offset(self) -> int: ...

    @property
    def limit(self) -> int: ...


class ScopeSearchInput(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def offset(self) -> int: ...

    @property
    def limit(self) -> int: ...


def meaning_search_query(
    service: TermKeeperService,
    query: MeaningSearchInput,
) -> SearchQuery:
    return SearchQuery(
        text=query.text,
        field=SearchField(query.field),
        tag=query.tag,
        scope=(
            service.get_scope_by_public_id(query.scope_id).name
            if query.scope_id is not None
            else None
        ),
        favorite_only=query.favorite_only,
        offset=query.offset,
        limit=query.limit,
    )


def occurrence_search_query(
    service: TermKeeperService,
    query: OccurrenceSearchInput,
) -> OccurrenceQuery:
    return OccurrenceQuery(
        meaning_id=(
            service.get_meaning_by_public_id(
                query.meaning_id,
                include_deleted=True,
            ).meaning_id
            if query.meaning_id is not None
            else None
        ),
        status=OccurrenceStatus(query.status) if query.status else None,
        text=query.text,
        source=query.source,
        since=query.since,
        offset=query.offset,
        limit=query.limit,
    )


def inbox_search_query(query: InboxSearchInput) -> OccurrenceQuery:
    return OccurrenceQuery(
        text=query.text,
        source=query.source,
        since=query.since,
        offset=query.offset,
        limit=query.limit,
    )


def scope_search_query(query: ScopeSearchInput) -> ScopeSearchQuery:
    return ScopeSearchQuery(
        text=query.text,
        offset=query.offset,
        limit=query.limit,
    )
