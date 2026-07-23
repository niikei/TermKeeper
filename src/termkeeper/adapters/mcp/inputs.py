"""Typed MCP input contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

type Offset = Annotated[
    int,
    Field(ge=0, description="Zero-based result offset; add returned item count for next page"),
]
type Limit = Annotated[int, Field(ge=1, le=100, description="Maximum items to return")]
type SearchText = Annotated[
    str,
    Field(min_length=1, description="Case-insensitive text to find; SQL wildcards are literal"),
]


@dataclass(frozen=True)
class OccurrenceFilters:
    meaning_id: UUID | None = None
    status: Literal["Pending", "Resolved", "Discarded"] | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    offset: Offset = 0
    limit: Limit = 50


@dataclass(frozen=True)
class OccurrenceSearchFilters:
    text: SearchText
    meaning_id: UUID | None = None
    status: Literal["Pending", "Resolved", "Discarded"] | None = None
    source: str | None = None
    since: datetime | None = None
    offset: Offset = 0
    limit: Limit = 20


@dataclass(frozen=True)
class InboxSearchFilters:
    text: SearchText
    source: str | None = None
    since: datetime | None = None
    offset: Offset = 0
    limit: Limit = 20


@dataclass(frozen=True)
class SearchFilters:
    text: SearchText
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    scope_id: UUID | None = None
    favorite_only: bool = False
    offset: Offset = 0
    limit: Limit = 20


@dataclass(frozen=True)
class ScopeSearchFilters:
    text: SearchText
    offset: Offset = 0
    limit: Limit = 20
