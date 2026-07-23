"""Stable use-case API for CLI, HTTP, and MCP adapters."""

from termkeeper.domain.models import AddResult, InboxItem, Meaning
from termkeeper.infrastructure import repository
from termkeeper.infrastructure.schema import init_db
from termkeeper.infrastructure.tables import Inbox as InboxRecord


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class TermKeeperService:
    def initialize(self) -> None:
        init_db()

    def add(self, keyword: str, memo: str | None = None, source: str | None = None) -> AddResult:
        keyword = keyword.strip()
        if not keyword:
            message = "Keyword must not be empty."
            raise ValidationError(message)
        registered = repository.find_registered_term(keyword)
        if registered:
            return AddResult(
                "registered",
                meaning=self.get_meaning(_required_id(registered.meaning_id)),
            )
        existing = repository.find_open_inbox(keyword)
        if existing:
            inbox_id = _required_id(existing.inbox_id)
            repository.touch_inbox(inbox_id, memo, source)
            return AddResult("seen_again", inbox=self.get_inbox(inbox_id))
        inbox_id = repository.add_inbox(keyword, memo, source)
        return AddResult("created", inbox=self.get_inbox(inbox_id))

    def get_inbox(self, inbox_id: int) -> InboxItem:
        row = repository.get_inbox(inbox_id)
        if not row:
            message = f"Inbox {inbox_id} was not found."
            raise NotFoundError(message)
        return _to_inbox(row)

    def inbox(self) -> list[InboxItem]:
        return [_to_inbox(row) for row in repository.list_inbox()]

    def history(self) -> list[InboxItem]:
        return [_to_inbox(row) for row in repository.list_history()]

    def resolve(self, inbox_id: int, full_name: str, description: str | None = None) -> Meaning:
        item = self.get_inbox(inbox_id)
        if item.status != "New":
            message = f"Inbox {inbox_id} is already {item.status}."
            raise ValidationError(message)
        full_name = full_name.strip()
        if not full_name:
            message = "Full name must not be empty."
            raise ValidationError(message)
        meaning_id = repository.create_meaning(full_name, description)
        repository.add_term(meaning_id, item.keyword)
        repository.add_term(meaning_id, full_name)
        repository.close_inbox(inbox_id, meaning_id)
        return self.get_meaning(meaning_id)

    def discard(self, inbox_id: int) -> None:
        if repository.discard_inbox(inbox_id) == 0:
            message = f"Open inbox {inbox_id} was not found."
            raise NotFoundError(message)

    def get_meaning(self, meaning_id: int) -> Meaning:
        row = repository.get_meaning(meaning_id)
        if not row:
            message = f"Meaning {meaning_id} was not found."
            raise NotFoundError(message)
        terms = tuple(term.keyword for term in repository.get_terms_by_meaning(meaning_id))
        return Meaning(
            _required_id(row.meaning_id),
            row.full_name,
            row.description,
            row.created_at,
            row.updated_at,
            terms,
        )

    def search(self, keyword: str) -> list[Meaning]:
        if not keyword.strip():
            message = "Search keyword must not be empty."
            raise ValidationError(message)
        return [
            self.get_meaning(_required_id(row.meaning_id))
            for row in repository.search_term(keyword)
        ]

    def meanings(self) -> list[Meaning]:
        return [
            self.get_meaning(_required_id(row.meaning_id)) for row in repository.list_meanings()
        ]

    def add_alias(self, meaning_id: int, keyword: str) -> Meaning:
        self.get_meaning(meaning_id)
        if not keyword.strip():
            message = "Alias must not be empty."
            raise ValidationError(message)
        repository.add_term(meaning_id, keyword)
        return self.get_meaning(meaning_id)

    def edit(self, meaning_id: int, full_name: str, description: str | None) -> Meaning:
        self.get_meaning(meaning_id)
        if not full_name.strip():
            message = "Full name must not be empty."
            raise ValidationError(message)
        repository.update_meaning(meaning_id, full_name, description)
        repository.add_term(meaning_id, full_name)
        return self.get_meaning(meaning_id)


def _required_id(value: int | None) -> int:
    if value is None:
        message = "A persisted record has no primary key."
        raise RuntimeError(message)
    return value


def _to_inbox(record: InboxRecord) -> InboxItem:
    return InboxItem(
        inbox_id=_required_id(record.inbox_id),
        keyword=record.keyword,
        status=record.status,
        memo=record.memo,
        source=record.source,
        occurrence_count=record.occurrence_count,
        created_at=record.created_at,
        updated_at=record.updated_at,
        last_seen_at=record.last_seen_at,
        closed_at=record.closed_at,
        resolved_meaning_id=record.resolved_meaning_id,
    )
