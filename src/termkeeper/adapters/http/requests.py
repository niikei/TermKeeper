"""HTTP request and query models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from termkeeper.domain import GENERAL_SCOPE_PUBLIC_ID


class CaptureRequest(BaseModel):
    keyword: str
    memo: str | None = None
    source: str | None = None
    meaning_id: UUID | None = None


class CaptureBatchRequest(BaseModel):
    items: tuple[CaptureRequest, ...] = Field(min_length=1, max_length=100)


class ResolveRequest(BaseModel):
    full_name: str
    scope_id: UUID = GENERAL_SCOPE_PUBLIC_ID
    description: str | None = None


class MeaningUpdateRequest(BaseModel):
    full_name: str
    scope_id: UUID
    description: str | None = None


class OccurrenceFilters(BaseModel):
    meaning_id: UUID | None = None
    status: Literal["Pending", "Resolved", "Discarded"] | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)


class OccurrenceSearchFilters(BaseModel):
    text: str = Field(min_length=1)
    meaning_id: UUID | None = None
    status: Literal["Pending", "Resolved", "Discarded"] | None = None
    source: str | None = None
    since: datetime | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class InboxSearchFilters(BaseModel):
    text: str = Field(min_length=1)
    source: str | None = None
    since: datetime | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class SearchFilters(BaseModel):
    text: str = Field(min_length=1)
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    scope_id: UUID | None = None
    favorite_only: bool = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ScopeSearchFilters(BaseModel):
    text: str = Field(min_length=1)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class OccurrenceUpdateRequest(BaseModel):
    keyword: str | None = None
    memo: str | None = None
    source: str | None = None
    clear_memo: bool = False
    clear_source: bool = False


class ReferenceCreateRequest(BaseModel):
    url: str
    title: str | None = None


class ReferenceUpdateRequest(BaseModel):
    url: str | None = None
    title: str | None = None
    clear_title: bool = False


class ScopeCreateRequest(BaseModel):
    name: str
    description: str | None = None


class ScopeUpdateRequest(BaseModel):
    name: str
    description: str | None = None
