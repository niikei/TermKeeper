"""Human-readable and JSON output rendering."""

import json

from termkeeper.domain import AddResult, InboxItem, Meaning
from termkeeper.presentation.types import CommandResult


def print_json(value: CommandResult) -> None:
    if isinstance(value, (AddResult, Meaning)):
        payload = value.to_dict()
    elif isinstance(value, list):
        payload = [item.to_dict() for item in value]
    else:
        payload = dict(value)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_inbox(items: list[InboxItem]) -> None:
    if not items:
        print("Inbox is empty.")
        return
    print(f"{'ID':>4}  {'Term':<24} {'Status':<9} {'Seen':>4}  Updated (UTC)")
    for item in items:
        print(
            f"{item.inbox_id:>4}  {item.keyword:<24.24} {item.status:<9} "
            f"{item.occurrence_count:>4}  {item.updated_at}",
        )
        details = " / ".join(value for value in (item.memo, item.source) if value)
        if details:
            print(f"      {details}")


def print_meaning(item: Meaning) -> None:
    print(f"[{item.meaning_id}] {item.full_name}")
    if item.description:
        print(item.description)
    if item.terms:
        print("Aliases: " + ", ".join(item.terms))
    print(f"Created: {item.created_at}  Updated: {item.updated_at}")
