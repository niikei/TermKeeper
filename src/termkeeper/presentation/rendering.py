"""Human-readable and JSON output rendering."""

import json

from termkeeper.domain import AddResult, InboxItem, Meaning, OccurrenceItem, SearchHit
from termkeeper.presentation.types import CommandResult


def print_json(value: CommandResult) -> None:
    if isinstance(value, (AddResult, Meaning)):
        _print_json_value(value.to_dict())
        return
    if isinstance(value, list):
        _print_json_value([item.to_dict() for item in value])
        return
    _print_json_value(dict(value))


def _print_json_value(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


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


def print_occurrences(items: list[OccurrenceItem]) -> None:
    if not items:
        print("No occurrences found.")
        return
    print(f"{'ID':>4}  {'Term':<24} {'Source':<16} Occurred (UTC)")
    for item in items:
        print(
            f"{item.occurrence_id:>4}  {item.keyword:<24.24} "
            f"{(item.source or '-'):<16.16} {item.occurred_at}",
        )
        details = [f"memo: {item.memo}"] if item.memo else []
        if item.inbox_id is not None:
            details.append(f"inbox: {item.inbox_id}")
        if item.meaning_id is not None:
            details.append(f"meaning: {item.meaning_id}")
        if details:
            print("      " + " / ".join(details))


def print_meaning(item: Meaning) -> None:
    print(f"[{item.meaning_id}] {item.full_name}")
    if item.description:
        print(item.description)
    if item.terms:
        print("Aliases: " + ", ".join(item.terms))
    print(f"Created: {item.created_at}  Updated: {item.updated_at}")


def print_search_hit(hit: SearchHit) -> None:
    print_meaning(hit.meaning)
    print(f"Match: {hit.matched_field} {hit.matched_text!r} (score: {hit.score})")
