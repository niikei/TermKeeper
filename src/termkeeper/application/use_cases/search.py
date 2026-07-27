"""Shared search use cases used by every inbound adapter."""

import regex

from termkeeper.application.errors import ValidationError
from termkeeper.application.mapping import to_meaning, to_occurrence, to_scope
from termkeeper.application.search import rank_search, rank_suggestions, search_tokens
from termkeeper.application.support import get_scope_by_name, required_id
from termkeeper.application.validation import optional_filter, to_utc, validate_page
from termkeeper.domain import (
    LogicalOperator,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceStatus,
    Page,
    Scope,
    ScopeSearchQuery,
    SearchHit,
    SearchMode,
    SearchQuery,
    SearchResult,
)
from termkeeper.infrastructure.normalization import normalize_keyword
from termkeeper.infrastructure.repositories import (
    meaning_repository,
    occurrence_repository,
    scope_repository,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork

MAX_SEARCH_LIMIT = 100
MAX_LIST_LIMIT = 500
MAX_SUGGESTION_LIMIT = 10
MAX_PATTERN_LENGTH = 256
MAX_PATTERN_SCAN = 10_000


class SearchUseCases:
    """Resource search boundary shared by CLI, HTTP, and MCP."""

    def search_meanings(self, query: SearchQuery | str) -> SearchResult:
        query = SearchQuery(query) if isinstance(query, str) else query
        text = query.text.strip()
        tokens = search_tokens(text)
        validate_page(
            query.offset,
            query.limit,
            resource="Meaning",
            max_limit=MAX_SEARCH_LIMIT,
        )
        if not text:
            message = "Search keyword must not be empty."
            raise ValidationError(message)
        if not query.fields:
            message = "At least one search field is required."
            raise ValidationError(message)
        if len(set(query.fields)) != len(query.fields):
            message = "Search fields must not contain duplicates."
            raise ValidationError(message)
        if query.mode != SearchMode.SMART and query.word_match != LogicalOperator.ALL:
            message = "Word matching can only be changed in smart search mode."
            raise ValidationError(message)
        if len(text) > MAX_PATTERN_LENGTH:
            message = f"Search text cannot exceed {MAX_PATTERN_LENGTH} characters."
            raise ValidationError(message)
        if not 0 <= query.suggestion_limit <= MAX_SUGGESTION_LIMIT:
            message = f"Suggestion limit must be between 0 and {MAX_SUGGESTION_LIMIT}."
            raise ValidationError(message)
        tag = optional_filter(query.tag, name="Tag")
        scope = optional_filter(query.scope, name="Scope")
        query = SearchQuery(
            text=text,
            mode=query.mode,
            fields=query.fields,
            word_match=query.word_match,
            offset=query.offset,
            limit=query.limit,
            tag=tag,
            scope=scope,
            favorite_only=query.favorite_only,
            suggestion_limit=query.suggestion_limit,
        )

        with UnitOfWork() as uow:
            scope_id = (
                required_id(get_scope_by_name(uow, query.scope).scope_id) if query.scope else None
            )
            if query.mode in {SearchMode.GLOB, SearchMode.REGEX}:
                records = meaning_repository.list_all(
                    uow.session,
                    scope_id=scope_id,
                    favorite_only=query.favorite_only,
                    tag=query.tag,
                    limit=MAX_PATTERN_SCAN + 1,
                )
                if len(records) > MAX_PATTERN_SCAN:
                    message = (
                        f"{query.mode.value} search is limited to "
                        f"{MAX_PATTERN_SCAN} candidate meanings."
                    )
                    raise ValidationError(message)
            else:
                values = (
                    tokens if query.mode == SearchMode.SMART else (normalize_keyword(query.text),)
                )
                records = meaning_repository.search(
                    uow.session,
                    values,
                    query.fields,
                    query.mode,
                    scope_id=scope_id,
                    favorite_only=query.favorite_only,
                    tag=query.tag,
                )
            meanings = [to_meaning(uow.session, row) for row in records]
            try:
                ranked = rank_search(meanings, query)
            except regex.error as exc:
                message = f"Invalid regular expression: {exc}."
                raise ValidationError(message) from exc
            except TimeoutError as exc:
                message = "Regular expression evaluation timed out."
                raise ValidationError(message) from exc
            if ranked:
                return _search_page(ranked, query)
            if query.mode != SearchMode.SMART or query.suggestion_limit == 0 or query.offset > 0:
                return _search_page([], query)
            all_meanings = [
                to_meaning(uow.session, row)
                for row in meaning_repository.list_all(
                    uow.session,
                    scope_id=scope_id,
                    favorite_only=query.favorite_only,
                    tag=query.tag,
                    limit=MAX_PATTERN_SCAN,
                )
            ]
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
        validate_page(
            query.offset,
            query.limit,
            resource="Scope",
            max_limit=MAX_SEARCH_LIMIT,
        )
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
    validate_page(
        query.offset,
        query.limit,
        resource="Occurrence",
        max_limit=max_limit,
    )
    keyword = optional_filter(query.keyword, name="Occurrence keyword")
    source = optional_filter(query.source, name="Occurrence source")
    normalized = OccurrenceQuery(
        meaning_id=query.meaning_id,
        status=query.status,
        text=query.text.strip() if query.text else None,
        keyword=keyword,
        source=source,
        since=to_utc(query.since),
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
