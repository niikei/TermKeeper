"""Stable external response models and mapping without database identifiers."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from termkeeper.application import NotFoundError, TermKeeperService
from termkeeper.domain import (
    AddResult,
    InboxItem,
    InboxStatus,
    Meaning,
    OccurrenceItem,
    ReferenceLink,
    SearchField,
    SearchResult,
)


@dataclass(frozen=True)
class ExternalPage[T]:
    items: tuple[T, ...]
    offset: int
    limit: int
    has_more: bool


def page[T](items: list[T], offset: int, limit: int) -> ExternalPage[T]:
    selected = items[offset : offset + limit + 1]
    return ExternalPage(
        items=tuple(selected[:limit]),
        offset=offset,
        limit=limit,
        has_more=len(selected) > limit,
    )


@dataclass(frozen=True)
class ExternalMeaning:
    public_id: UUID
    full_name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    is_favorite: bool
    terms: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ExternalInbox:
    public_id: UUID
    keyword: str
    status: InboxStatus
    memo: str | None
    source: str | None
    occurrence_count: int
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    closed_at: datetime | None
    resolved_meaning_id: UUID | None


@dataclass(frozen=True)
class ExternalOccurrence:
    public_id: UUID
    keyword: str
    memo: str | None
    source: str | None
    occurred_at: datetime
    updated_at: datetime
    inbox_id: UUID | None
    meaning_id: UUID | None


@dataclass(frozen=True)
class ExternalReference:
    public_id: UUID
    meaning_id: UUID
    url: str
    title: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ExternalAddResult:
    outcome: str
    inbox: ExternalInbox | None = None
    meaning: ExternalMeaning | None = None


@dataclass(frozen=True)
class ExternalSearchHit:
    meaning: ExternalMeaning
    score: int
    matched_field: SearchField
    matched_text: str


@dataclass(frozen=True)
class ExternalSearchSuggestion:
    meaning: ExternalMeaning
    similarity: int
    matched_field: SearchField
    matched_text: str


@dataclass(frozen=True)
class ExternalSearchResult:
    hits: tuple[ExternalSearchHit, ...]
    suggestions: tuple[ExternalSearchSuggestion, ...]
    offset: int
    limit: int
    has_more: bool


class ExternalMapper:
    def __init__(self, service: TermKeeperService) -> None:
        self._service = service

    def meaning(self, item: Meaning) -> ExternalMeaning:
        return ExternalMeaning(
            public_id=item.public_id,
            full_name=item.full_name,
            description=item.description,
            created_at=item.created_at,
            updated_at=item.updated_at,
            deleted_at=item.deleted_at,
            is_favorite=item.is_favorite,
            terms=item.terms,
            tags=item.tags,
        )

    def inbox(self, item: InboxItem) -> ExternalInbox:
        return ExternalInbox(
            public_id=item.public_id,
            keyword=item.keyword,
            status=item.status,
            memo=item.memo,
            source=item.source,
            occurrence_count=item.occurrence_count,
            created_at=item.created_at,
            updated_at=item.updated_at,
            last_seen_at=item.last_seen_at,
            closed_at=item.closed_at,
            resolved_meaning_id=self._meaning_public_id(item.resolved_meaning_id),
        )

    def occurrence(self, item: OccurrenceItem) -> ExternalOccurrence:
        return ExternalOccurrence(
            public_id=item.public_id,
            keyword=item.keyword,
            memo=item.memo,
            source=item.source,
            occurred_at=item.occurred_at,
            updated_at=item.updated_at,
            inbox_id=self._inbox_public_id(item.inbox_id),
            meaning_id=self._meaning_public_id(item.meaning_id),
        )

    def reference(self, item: ReferenceLink) -> ExternalReference:
        meaning_id = self._meaning_public_id(item.meaning_id)
        if meaning_id is None:  # pragma: no cover - protected by the foreign key
            message = "Reference has no meaning."
            raise RuntimeError(message)
        return ExternalReference(
            public_id=item.public_id,
            meaning_id=meaning_id,
            url=item.url,
            title=item.title,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def add_result(self, result: AddResult) -> ExternalAddResult:
        return ExternalAddResult(
            outcome=result.outcome,
            inbox=self.inbox(result.inbox) if result.inbox is not None else None,
            meaning=self.meaning(result.meaning) if result.meaning is not None else None,
        )

    def search_result(
        self,
        result: SearchResult,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> ExternalSearchResult:
        hits = result.hits[offset : offset + limit + 1]
        return ExternalSearchResult(
            hits=tuple(
                ExternalSearchHit(
                    meaning=self.meaning(hit.meaning),
                    score=hit.score,
                    matched_field=hit.matched_field,
                    matched_text=hit.matched_text,
                )
                for hit in hits[:limit]
            ),
            suggestions=tuple(
                ExternalSearchSuggestion(
                    meaning=self.meaning(item.meaning),
                    similarity=item.similarity,
                    matched_field=item.matched_field,
                    matched_text=item.matched_text,
                )
                for item in result.suggestions
            ),
            offset=offset,
            limit=limit,
            has_more=len(hits) > limit,
        )

    def _meaning_public_id(self, local_id: int | None) -> UUID | None:
        if local_id is None:
            return None
        try:
            return self._service.get_meaning(local_id).public_id
        except NotFoundError:
            return next(
                (item.public_id for item in self._service.trash() if item.meaning_id == local_id),
                None,
            )

    def _inbox_public_id(self, local_id: int | None) -> UUID | None:
        if local_id is None:
            return None
        return self._service.get_inbox(local_id).public_id
