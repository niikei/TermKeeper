"""Typed MCP input contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from termkeeper.domain import GENERAL_SCOPE_PUBLIC_ID

type Offset = Annotated[
    int,
    Field(ge=0, description="Zero-based result offset; add returned item count for next page"),
]
type Limit = Annotated[int, Field(ge=1, le=100, description="Maximum items to return")]
type SearchText = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r".*\S.*",
        description="Non-blank search text or pattern; surrounding whitespace is ignored",
    ),
]
type NonEmptyText = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r".*\S.*",
        description="Non-blank text; surrounding whitespace is normalized",
    ),
]
type CaptureItems = Annotated[
    tuple["CaptureTermInput", ...],
    Field(min_length=1, max_length=100, description="Terms captured in input order"),
]


@dataclass(frozen=True)
class CaptureTermInput:
    keyword: NonEmptyText
    memo: str | None = None
    source: str | None = None
    meaning_id: UUID | None = None


@dataclass(frozen=True)
class CaptureBatchInput:
    items: CaptureItems


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
    mode: Annotated[
        Literal["smart", "exact", "prefix", "contains", "glob", "regex"],
        Field(description="Matching algorithm; smart is ranked word search"),
    ] = "smart"
    fields: Annotated[
        tuple[Literal["term", "name", "description"], ...],
        Field(
            min_length=1,
            description="Fields are combined with OR; include each field at most once",
        ),
    ] = ("term", "name", "description")
    word_match: Annotated[
        Literal["all", "any"],
        Field(description="In smart mode, require all or any words across selected fields"),
    ] = "all"
    tag: str | None = None
    scope_id: UUID | None = None
    favorite_only: bool = False
    offset: Offset = 0
    limit: Limit = 20
    suggestion_limit: Annotated[
        int,
        Field(
            ge=0,
            le=10,
            description="Smart-mode suggestions returned when the first page has no hits",
        ),
    ] = 3


@dataclass(frozen=True)
class MeaningFilters:
    tags: tuple[str, ...] = ()
    tag_match: Literal["all", "any"] = "all"
    scope_id: UUID | None = None
    favorite_only: bool = False
    created_since: datetime | None = None
    updated_since: datetime | None = None
    has_description: bool | None = None
    has_alias: bool | None = None
    sort: Literal["name", "created", "updated"] = "updated"
    order: Literal["asc", "desc"] = "desc"
    offset: Offset = 0
    limit: Limit = 20


@dataclass(frozen=True)
class MeaningCreateInput:
    full_name: NonEmptyText
    scope_id: UUID = GENERAL_SCOPE_PUBLIC_ID
    description: str | None = None
    aliases: tuple[NonEmptyText, ...] = ()


@dataclass(frozen=True)
class MeaningEditInput:
    full_name: NonEmptyText
    scope_id: UUID = GENERAL_SCOPE_PUBLIC_ID
    description: str | None = None


@dataclass(frozen=True)
class ScopeSearchFilters:
    text: SearchText
    offset: Offset = 0
    limit: Limit = 20
