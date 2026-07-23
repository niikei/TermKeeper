"""Shared search use cases used by every inbound adapter."""

from datetime import UTC, datetime

from termkeeper.application.errors import ValidationError
from termkeeper.application.mapping import to_meaning, to_occurrence, to_scope
from termkeeper.application.search import rank_search, rank_suggestions, search_tokens
from termkeeper.application.support import get_scope_by_name, required_id
from termkeeper.domain import (
    Meaning,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceStatus,
    Page,
    Scope,
    ScopeSearchQuery,
    SearchHit,
    SearchQuery,
    SearchResult,
)
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    scope_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork

MAX_SEARCH_LIMIT = 100
MAX_LIST_LIMIT = 500
MAX_SUGGESTION_LIMIT = 10


class SearchUseCases:
    """Resource search boundary shared by CLI, HTTP, and MCP."""

    def search_meanings(self, query: SearchQuery | str) -> SearchResult:
        query = SearchQuery(query) if isinstance(query, str) else query
        tokens = search_tokens(query.text)
        _validate_page(query.offset, query.limit, resource="Meaning")
        if not tokens:
            message = "Search keyword must not be empty."
            raise ValidationError(message)
        if not 0 <= query.suggestion_limit <= MAX_SUGGESTION_LIMIT:
            message = f"Suggestion limit must be between 0 and {MAX_SUGGESTION_LIMIT}."
            raise ValidationError(message)

        with UnitOfWork() as uow:
            scope_id = (
                required_id(get_scope_by_name(uow, query.scope).scope_id)
                if query.scope
                else None
            )
            records = meaning_repository.search(
                uow.session,
                tokens,
                query.field,
                scope_id=scope_id,
                favorite_only=query.favorite_only,
            )
            meanings = _filter_tag(
                [to_meaning(uow.session, row) for row in records],
                query.tag,
            )
            ranked = rank_search(meanings, query)
            if ranked:
                return _search_page(ranked, query)
            if query.suggestion_limit == 0:
                return _search_page([], query)
            all_meanings = _filter_tag(
                [
                    to_meaning(uow.session, row)
                    for row in meaning_repository.list_all(
                        uow.session,
                        scope_id=scope_id,
                        favorite_only=query.favorite_only,
                    )
                ],
                query.tag,
            )
            return SearchResult(
                (),
                tuple(rank_suggestions(all_meanings, query)),
                offset=query.offset,
                limit=query.limit,
            )

    def search_occurrences(self, query: OccurrenceQuery) -> Page[OccurrenceItem]:
        if query.text is None or not query.text.strip():
            message = "Occurrence search text must not be empty."
            raise ValidationError(message)
        return _occurrence_page(query, max_limit=MAX_SEARCH_LIMIT)

    def search_inbox(self, query: OccurrenceQuery) -> Page[OccurrenceItem]:
        return self.search_occurrences(
            OccurrenceQuery(
                status=OccurrenceStatus.PENDING,
                text=query.text,
                source=query.source,
                since=query.since,
                offset=query.offset,
                limit=query.limit,
            ),
        )

    def search_scopes(self, query: ScopeSearchQuery | str) -> Page[Scope]:
        query = ScopeSearchQuery(query) if isinstance(query, str) else query
        if not query.text.strip():
            message = "Scope search text must not be empty."
            raise ValidationError(message)
        _validate_page(query.offset, query.limit, resource="Scope")
        with UnitOfWork() as uow:
            records = scope_repository.search(
                uow.session,
                query.text.strip(),
                offset=query.offset,
                limit=query.limit,
            )
            return Page(
                items=tuple(to_scope(record) for record in records[: query.limit]),
                offset=query.offset,
                limit=query.limit,
                has_more=len(records) > query.limit,
            )


def occurrence_page(query: OccurrenceQuery) -> Page[OccurrenceItem]:
    """Execute an occurrence query for list-oriented use cases."""
    return _occurrence_page(query, max_limit=MAX_LIST_LIMIT)


def _occurrence_page(
    query: OccurrenceQuery,
    *,
    max_limit: int,
) -> Page[OccurrenceItem]:
    _validate_page(
        query.offset,
        query.limit,
        resource="Occurrence",
        max_limit=max_limit,
    )
    normalized = OccurrenceQuery(
        meaning_id=query.meaning_id,
        status=query.status,
        text=query.text.strip() if query.text else None,
        keyword=query.keyword.strip() if query.keyword else None,
        source=query.source.strip() if query.source else None,
        since=_to_utc(query.since),
        offset=query.offset,
        limit=query.limit,
    )
    with UnitOfWork() as uow:
        records = occurrence_repository.list_occurrences(uow.session, normalized)
        return Page(
            items=tuple(to_occurrence(row) for row in records[: normalized.limit]),
            offset=normalized.offset,
            limit=normalized.limit,
            has_more=len(records) > normalized.limit,
        )


def _search_page(hits: list[SearchHit], query: SearchQuery) -> SearchResult:
    page = hits[query.offset : query.offset + query.limit + 1]
    return SearchResult(
        hits=tuple(page[: query.limit]),
        offset=query.offset,
        limit=query.limit,
        has_more=len(page) > query.limit,
    )


def _validate_page(
    offset: int,
    limit: int,
    *,
    resource: str,
    max_limit: int = MAX_SEARCH_LIMIT,
) -> None:
    if offset < 0:
        message = f"{resource} offset must not be negative."
        raise ValidationError(message)
    if not 1 <= limit <= max_limit:
        message = f"{resource} limit must be between 1 and {max_limit}."
        raise ValidationError(message)


def _filter_tag(meanings: list[Meaning], tag: str | None) -> list[Meaning]:
    if tag is None:
        return meanings
    normalized = tag.strip().casefold()
    return [
        meaning
        for meaning in meanings
        if any(item.casefold() == normalized for item in meaning.tags)
    ]


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
