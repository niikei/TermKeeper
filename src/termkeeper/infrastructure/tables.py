"""Typed SQLModel tables for a fresh TermKeeper database."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from termkeeper.domain.status import OccurrenceStatus
from termkeeper.infrastructure.types import UTCDateTime


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserProfile(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    email: str | None = None
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)


class Scope(SQLModel, table=True):
    __table_args__ = (CheckConstraint("length(trim(name)) > 0"),)

    scope_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    name: str
    name_norm: str = Field(unique=True, index=True)
    description: str | None = None
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Meaning(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("length(trim(full_name)) > 0"),
        Index(
            "uq_meaning_active_scope_name",
            "scope_id",
            "full_name_norm",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    meaning_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    full_name: str
    full_name_norm: str
    scope_id: int = Field(foreign_key="scope.scope_id", ondelete="RESTRICT", index=True)
    description: str | None = None
    description_norm: str = ""
    is_favorite: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    deleted_at: datetime | None = Field(default=None, index=True, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    deleted_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Term(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("keyword_norm", "meaning_id"),
        Index("idx_term_keyword", "keyword_norm"),
        Index("idx_term_meaning", "meaning_id"),
    )

    term_id: int | None = Field(default=None, primary_key=True)
    meaning_id: int = Field(foreign_key="meaning.meaning_id", ondelete="CASCADE")
    keyword: str
    keyword_norm: str
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Tag(SQLModel, table=True):
    tag_id: int | None = Field(default=None, primary_key=True)
    name: str
    name_norm: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class MeaningTag(SQLModel, table=True):
    meaning_id: int = Field(
        primary_key=True,
        foreign_key="meaning.meaning_id",
        ondelete="CASCADE",
    )
    tag_id: int = Field(primary_key=True, foreign_key="tag.tag_id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class MeaningRelation(SQLModel, table=True):
    __table_args__ = (CheckConstraint("meaning_id_low < meaning_id_high"),)

    meaning_id_low: int = Field(
        primary_key=True,
        foreign_key="meaning.meaning_id",
        ondelete="CASCADE",
    )
    meaning_id_high: int = Field(
        primary_key=True,
        foreign_key="meaning.meaning_id",
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class MeaningReference(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("length(trim(url)) > 0"),
        UniqueConstraint("meaning_id", "url"),
    )

    reference_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    meaning_id: int = Field(foreign_key="meaning.meaning_id", ondelete="CASCADE", index=True)
    url: str
    title: str | None = None
    created_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Occurrence(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("length(trim(keyword)) > 0"),
        CheckConstraint(
            "(status = 'PENDING' AND meaning_id IS NULL) OR "
            "(status = 'RESOLVED' AND meaning_id IS NOT NULL) OR "
            "(status = 'DISCARDED' AND meaning_id IS NULL)",
            name="ck_occurrence_status_meaning",
        ),
    )

    occurrence_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    keyword: str
    keyword_norm: str = Field(index=True)
    status: OccurrenceStatus = Field(default=OccurrenceStatus.PENDING, index=True)
    meaning_id: int | None = Field(
        default=None,
        foreign_key="meaning.meaning_id",
        ondelete="RESTRICT",
    )
    memo: str | None = None
    source: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now, index=True, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utc_now, sa_type=UTCDateTime)
    resolved_at: datetime | None = Field(default=None, sa_type=UTCDateTime)
    discarded_at: datetime | None = Field(default=None, sa_type=UTCDateTime)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    resolved_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    discarded_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
