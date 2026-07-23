"""Typed MCP input contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

type Offset = Annotated[int, Field(ge=0)]
type Limit = Annotated[int, Field(ge=1, le=100)]


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
class SearchFilters:
    text: str
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    scope: str | None = None
    favorite_only: bool = False
    offset: Offset = 0
    limit: Limit = 20
