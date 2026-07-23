"""SQLModel table definitions for the SQLite persistence adapter."""

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


class Meaning(SQLModel, table=True):
    __table_args__ = (CheckConstraint("length(trim(full_name)) > 0"),)

    meaning_id: int | None = Field(default=None, primary_key=True)
    full_name: str
    description: str | None = None
    created_at: str
    updated_at: str


class Inbox(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("length(trim(keyword)) > 0"),
        CheckConstraint("status IN ('New', 'Closed', 'Discarded')"),
        Index("idx_inbox_open_keyword", "keyword_norm", "status"),
    )

    inbox_id: int | None = Field(default=None, primary_key=True)
    keyword: str
    keyword_norm: str
    memo: str | None = None
    source: str | None = None
    status: str = "New"
    resolved_meaning_id: int | None = Field(default=None, foreign_key="meaning.meaning_id")
    occurrence_count: int = 1
    created_at: str
    updated_at: str
    last_seen_at: str
    closed_at: str | None = None


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
    created_at: str
    updated_at: str


class AppSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
    updated_at: str
