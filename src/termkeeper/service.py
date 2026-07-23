"""Application use cases: stable entry point for CLI, API, and MCP adapters."""

from termkeeper import db
from termkeeper.models import AddResult, InboxItem, Meaning


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class TermKeeperService:
    def initialize(self) -> None:
        db.init_db()

    def add(self, keyword: str, memo: str | None = None, source: str | None = None) -> AddResult:
        keyword = keyword.strip()
        if not keyword:
            raise ValidationError("Keyword must not be empty.")
        registered = db.find_registered_term(keyword)
        if registered:
            return AddResult("registered", meaning=self.get_meaning(registered["meaning_id"]))
        existing = db.find_open_inbox(keyword)
        if existing:
            db.touch_inbox(existing["inbox_id"], memo, source)
            return AddResult("seen_again", inbox=self.get_inbox(existing["inbox_id"]))
        inbox_id = db.add_inbox(keyword, memo, source)
        return AddResult("created", inbox=self.get_inbox(inbox_id))

    def get_inbox(self, inbox_id: int) -> InboxItem:
        row = db.get_inbox(inbox_id)
        if not row:
            raise NotFoundError(f"Inbox {inbox_id} was not found.")
        return InboxItem.from_row(row)

    def inbox(self) -> list[InboxItem]:
        return [InboxItem.from_row(row) for row in db.list_inbox()]

    def history(self) -> list[InboxItem]:
        return [InboxItem.from_row(row) for row in db.list_history()]

    def resolve(self, inbox_id: int, full_name: str, description: str | None = None) -> Meaning:
        item = self.get_inbox(inbox_id)
        if item.status not in ("New", "Pending"):
            raise ValidationError(f"Inbox {inbox_id} is already {item.status}.")
        full_name = full_name.strip()
        if not full_name:
            raise ValidationError("Full name must not be empty.")
        meaning_id = db.create_meaning(full_name, description)
        db.add_term(meaning_id, item.keyword)
        db.add_term(meaning_id, full_name)
        db.close_inbox(inbox_id, meaning_id)
        return self.get_meaning(meaning_id)

    def discard(self, inbox_id: int) -> None:
        if db.discard_inbox(inbox_id) == 0:
            raise NotFoundError(f"Open inbox {inbox_id} was not found.")

    def get_meaning(self, meaning_id: int) -> Meaning:
        row = db.get_meaning(meaning_id)
        if not row:
            raise NotFoundError(f"Meaning {meaning_id} was not found.")
        terms = tuple(term["keyword"] for term in db.get_terms_by_meaning(meaning_id))
        return Meaning(
            row["meaning_id"],
            row["full_name"],
            row["description"],
            row["created_at"],
            row["updated_at"],
            terms,
        )

    def search(self, keyword: str) -> list[Meaning]:
        if not keyword.strip():
            raise ValidationError("Search keyword must not be empty.")
        return [self.get_meaning(row["meaning_id"]) for row in db.search_term(keyword)]

    def meanings(self) -> list[Meaning]:
        return [self.get_meaning(row["meaning_id"]) for row in db.list_meanings()]

    def add_alias(self, meaning_id: int, keyword: str) -> Meaning:
        self.get_meaning(meaning_id)
        if not keyword.strip():
            raise ValidationError("Alias must not be empty.")
        db.add_term(meaning_id, keyword)
        return self.get_meaning(meaning_id)

    def edit(self, meaning_id: int, full_name: str, description: str | None) -> Meaning:
        self.get_meaning(meaning_id)
        if not full_name.strip():
            raise ValidationError("Full name must not be empty.")
        db.update_meaning(meaning_id, full_name, description)
        db.add_term(meaning_id, full_name)
        return self.get_meaning(meaning_id)
