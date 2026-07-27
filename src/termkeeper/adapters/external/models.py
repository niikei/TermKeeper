"""Stable external response models and mapping without database identifiers."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    CaptureBatchResult,
    CaptureResult,
    Meaning,
    OccurrenceItem,
    OccurrenceStatus,
    Page,
    ReferenceLink,
    Scope,
    SearchField,
    SearchResult,
)


@dataclass(frozen=True)
class ExternalPage[T]:
    items: tuple[T, ...]
    offset: int
    limit: int
    has_more: bool


@dataclass(frozen=True)
class ExternalMeaning:
    public_id: UUID
    full_name: str
    scope_id: UUID
    scope: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    is_favorite: bool
    terms: tuple[str, ...]
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ExternalOccurrence:
    public_id: UUID
    keyword: str
    memo: str | None
    source: str | None
    status: OccurrenceStatus
    occurred_at: datetime
    updated_at: datetime
    meaning_id: UUID | None
    resolved_at: datetime | None
    discarded_at: datetime | None


@dataclass(frozen=True)
class ExternalReference:
    public_id: UUID
    meaning_id: UUID
    url: str
    title: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ExternalScope:
    public_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ExternalCaptureResult:
    occurrence: ExternalOccurrence
    candidates: tuple[ExternalMeaning, ...]


@dataclass(frozen=True)
class ExternalCaptureBatchResult:
    items: tuple[ExternalCaptureResult, ...]


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
            scope_id=item.scope_public_id,
            scope=item.scope,
            description=item.description,
            created_at=item.created_at,
            updated_at=item.updated_at,
            deleted_at=item.deleted_at,
            is_favorite=item.is_favorite,
            terms=item.terms,
            tags=item.tags,
        )

    def scope(self, item: Scope) -> ExternalScope:
        return ExternalScope(
            public_id=item.public_id,
            name=item.name,
            description=item.description,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def scope_page(self, result: Page[Scope]) -> ExternalPage[ExternalScope]:
        return ExternalPage(
            items=tuple(self.scope(item) for item in result.items),
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
        )

    def occurrence(self, item: OccurrenceItem) -> ExternalOccurrence:
        public_ids = self._meaning_public_ids((item.meaning_id,))
        return self._occurrence(item, public_ids)

    def _occurrence(
        self,
        item: OccurrenceItem,
        public_ids: Mapping[int, UUID],
    ) -> ExternalOccurrence:
        return ExternalOccurrence(
            public_id=item.public_id,
            keyword=item.keyword,
            memo=item.memo,
            source=item.source,
            status=item.status,
            occurred_at=item.occurred_at,
            updated_at=item.updated_at,
            meaning_id=public_ids.get(item.meaning_id) if item.meaning_id is not None else None,
            resolved_at=item.resolved_at,
            discarded_at=item.discarded_at,
        )

    def occurrence_page(
        self,
        result: Page[OccurrenceItem],
    ) -> ExternalPage[ExternalOccurrence]:
        public_ids = self._meaning_public_ids(item.meaning_id for item in result.items)
        return ExternalPage(
            items=tuple(self._occurrence(item, public_ids) for item in result.items),
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
        )

    def reference(self, item: ReferenceLink) -> ExternalReference:
        public_ids = self._meaning_public_ids((item.meaning_id,))
        return self._reference(item, public_ids)

    def references(self, items: list[ReferenceLink]) -> list[ExternalReference]:
        public_ids = self._meaning_public_ids(item.meaning_id for item in items)
        return [self._reference(item, public_ids) for item in items]

    def _reference(
        self,
        item: ReferenceLink,
        public_ids: Mapping[int, UUID],
    ) -> ExternalReference:
        meaning_id = public_ids.get(item.meaning_id)
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

    def capture_result(self, result: CaptureResult) -> ExternalCaptureResult:
        public_ids = self._meaning_public_ids((result.occurrence.meaning_id,))
        return self._capture_result(result, public_ids)

    def capture_batch(
        self,
        result: CaptureBatchResult,
    ) -> ExternalCaptureBatchResult:
        public_ids = self._meaning_public_ids(item.occurrence.meaning_id for item in result.items)
        return ExternalCaptureBatchResult(
            items=tuple(self._capture_result(item, public_ids) for item in result.items),
        )

    def _capture_result(
        self,
        result: CaptureResult,
        public_ids: Mapping[int, UUID],
    ) -> ExternalCaptureResult:
        return ExternalCaptureResult(
            occurrence=self._occurrence(result.occurrence, public_ids),
            candidates=tuple(self.meaning(item) for item in result.candidates),
        )

    def meaning_page(self, result: Page[Meaning]) -> ExternalPage[ExternalMeaning]:
        return ExternalPage(
            items=tuple(self.meaning(item) for item in result.items),
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
        )

    def reference_page(
        self,
        result: Page[ReferenceLink],
    ) -> ExternalPage[ExternalReference]:
        public_ids = self._meaning_public_ids(reference.meaning_id for reference in result.items)
        return ExternalPage(
            items=tuple(self._reference(reference, public_ids) for reference in result.items),
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
        )

    def search_result(
        self,
        result: SearchResult,
    ) -> ExternalSearchResult:
        return ExternalSearchResult(
            hits=tuple(
                ExternalSearchHit(
                    meaning=self.meaning(hit.meaning),
                    score=hit.score,
                    matched_field=hit.matched_field,
                    matched_text=hit.matched_text,
                )
                for hit in result.hits
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
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
        )

    def _meaning_public_ids(self, local_ids: Iterable[int | None]) -> dict[int, UUID]:
        return self._service.meaning_public_ids(
            {local_id for local_id in local_ids if local_id is not None},
        )
