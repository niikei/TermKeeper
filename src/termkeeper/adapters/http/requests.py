"""HTTP request and query models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CaptureRequest(BaseModel):
    keyword: str
    memo: str | None = None
    source: str | None = None


class ResolveRequest(BaseModel):
    full_name: str
    description: str | None = None


class MeaningUpdateRequest(BaseModel):
    full_name: str
    description: str | None = None


class OccurrenceFilters(BaseModel):
    meaning_id: UUID | None = None
    inbox_id: UUID | None = None
    keyword: str | None = None
    source: str | None = None
    since: datetime | None = None
    offset: int = Field(default=0, ge=0, le=399)
    limit: int = Field(default=50, ge=1, le=100)


class SearchFilters(BaseModel):
    text: str = Field(min_length=1)
    field: Literal["all", "term", "name", "description"] = "all"
    tag: str | None = None
    favorite_only: bool = False
    offset: int = Field(default=0, ge=0, le=399)
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
