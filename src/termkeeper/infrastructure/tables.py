"""Typed SQLModel tables for a fresh TermKeeper database."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text
from sqlmodel import Field, SQLModel

from termkeeper.domain.status import InboxStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserProfile(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    email: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Meaning(SQLModel, table=True):
    __table_args__ = (CheckConstraint("length(trim(full_name)) > 0"),)

    meaning_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    full_name: str
    description: str | None = None
    is_favorite: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deleted_at: datetime | None = Field(default=None, index=True)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    deleted_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Inbox(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("length(trim(keyword)) > 0"),
        Index(
            "uq_inbox_open_keyword",
            "keyword_norm",
            unique=True,
            sqlite_where=text("status = 'NEW'"),
        ),
    )

    inbox_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    keyword: str
    keyword_norm: str
    status: InboxStatus = InboxStatus.NEW
    resolved_meaning_id: int | None = Field(
        default=None,
        foreign_key="meaning.meaning_id",
        ondelete="SET NULL",
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    closed_at: datetime | None = None
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


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
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Tag(SQLModel, table=True):
    tag_id: int | None = Field(default=None, primary_key=True)
    name: str
    name_norm: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class MeaningTag(SQLModel, table=True):
    meaning_id: int = Field(
        primary_key=True,
        foreign_key="meaning.meaning_id",
        ondelete="CASCADE",
    )
    tag_id: int = Field(primary_key=True, foreign_key="tag.tag_id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utc_now)
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
    created_at: datetime = Field(default_factory=utc_now)
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
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")


class Occurrence(SQLModel, table=True):
    occurrence_id: int | None = Field(default=None, primary_key=True)
    public_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    keyword: str
    keyword_norm: str = Field(index=True)
    inbox_id: int | None = Field(default=None, foreign_key="inbox.inbox_id")
    meaning_id: int | None = Field(
        default=None,
        foreign_key="meaning.meaning_id",
        ondelete="SET NULL",
    )
    memo: str | None = None
    source: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
    updated_by_id: int | None = Field(default=None, foreign_key="userprofile.user_id")
