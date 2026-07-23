"""Human-readable and JSON output rendering."""

import json

from termkeeper.domain import (
    AddResult,
    ImportResult,
    InboxItem,
    Meaning,
    MergeResult,
    OccurrenceItem,
    SearchHit,
    SearchResult,
    SearchSuggestion,
    StatsSummary,
)
from termkeeper.presentation.types import CommandResult


def print_json(value: CommandResult) -> None:
    if isinstance(
        value,
        (
            AddResult,
            ImportResult,
            InboxItem,
            Meaning,
            MergeResult,
            OccurrenceItem,
            SearchResult,
            StatsSummary,
        ),
    ):
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


def print_stats(stats: StatsSummary) -> None:
    print(
        f"Occurrences: {stats.total_occurrences}  Open inbox: {stats.open_inbox_items}  "
        f"Meanings: {stats.active_meanings}",
    )
    print("Top terms:")
    for item in stats.top_terms:
        print(f"  {item.value}: {item.count} (last seen: {item.last_seen_at})")
    print("Top sources:")
    for item in stats.top_sources:
        print(f"  {item.value}: {item.count} (last seen: {item.last_seen_at})")


def print_meaning(item: Meaning) -> None:
    marker = "★ " if item.is_favorite else ""
    print(f"[{item.meaning_id}] {marker}{item.full_name}")
    if item.description:
        print(item.description)
    if item.terms:
        print("Aliases: " + ", ".join(item.terms))
    if item.tags:
        print("Tags: " + ", ".join(item.tags))
    if item.deleted_at:
        print(f"Deleted: {item.deleted_at}")
    print(f"Created: {item.created_at}  Updated: {item.updated_at}")


def print_search_hit(hit: SearchHit) -> None:
    print_meaning(hit.meaning)
    print(f"Match: {hit.matched_field} {hit.matched_text!r} (score: {hit.score})")


def print_search_suggestion(suggestion: SearchSuggestion) -> None:
    print(
        f"  [{suggestion.meaning.meaning_id}] {suggestion.meaning.full_name} "
        f"({suggestion.similarity}% via {suggestion.matched_field} "
        f"{suggestion.matched_text!r})",
    )
