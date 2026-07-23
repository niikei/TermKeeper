"""Human-readable and JSON output rendering."""

import json
from collections.abc import Sequence

from termkeeper.domain import (
    CaptureResult,
    ImportResult,
    Meaning,
    MergeResult,
    OccurrenceItem,
    Page,
    ReferenceLink,
    Scope,
    SearchHit,
    SearchResult,
    SearchSuggestion,
    StatsSummary,
)
from termkeeper.presentation.cli.types import CommandResult


def print_json(value: CommandResult) -> None:
    if isinstance(
        value,
        (
            CaptureResult,
            ImportResult,
            Meaning,
            MergeResult,
            OccurrenceItem,
            Page,
            ReferenceLink,
            SearchResult,
            Scope,
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


def print_inbox(items: Sequence[OccurrenceItem]) -> None:
    if not items:
        print("Inbox is empty.")
        return
    print(f"{'ID':>4}  {'Term':<24} {'Source':<16} Occurred (UTC)")
    for item in items:
        print(
            f"{item.occurrence_id:>4}  {item.keyword:<24.24} "
            f"{(item.source or '-'):<16.16} {item.occurred_at}",
        )
        details = " / ".join(value for value in (item.memo, item.source) if value)
        if details:
            print(f"      {details}")


def print_occurrences(items: Sequence[OccurrenceItem]) -> None:
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
        details.append(f"status: {item.status}")
        if item.meaning_id is not None:
            details.append(f"meaning: {item.meaning_id}")
        if details:
            print("      " + " / ".join(details))


def print_has_more(result: Page[OccurrenceItem]) -> None:
    if result.has_more:
        next_offset = result.offset + len(result.items)
        print(f"More items are available. Continue with --offset {next_offset}.")


def print_stats(stats: StatsSummary) -> None:
    print(
        f"Occurrences: {stats.total_occurrences}  Pending: {stats.pending_occurrences}  "
        f"Meanings: {stats.active_meanings}",
    )
    print("Top terms:")
    for item in stats.top_terms:
        print(f"  {item.value}: {item.count} (last seen: {item.last_seen_at})")
    print("Top sources:")
    for item in stats.top_sources:
        print(f"  {item.value}: {item.count} (last seen: {item.last_seen_at})")


def print_references(items: list[ReferenceLink]) -> None:
    for item in items:
        label = item.title or item.url
        print(f"[{item.reference_id}] {label}")
        if item.title:
            print(f"    {item.url}")


def print_meaning(item: Meaning) -> None:
    marker = "★ " if item.is_favorite else ""
    print(f"[{item.meaning_id}] {marker}{item.full_name} [{item.scope}]")
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
    marker = "★ " if hit.meaning.is_favorite else ""
    print(
        f"[{hit.meaning.meaning_id}] {marker}{hit.meaning.full_name} "
        f"[{hit.meaning.scope}]",
    )
    print(f"    {hit.matched_field}: {hit.matched_text!r} · score {hit.score}")


def print_search_suggestion(suggestion: SearchSuggestion) -> None:
    print(
        f"  [{suggestion.meaning.meaning_id}] {suggestion.meaning.full_name} "
        f"[{suggestion.meaning.scope}] "
        f"({suggestion.similarity}% via {suggestion.matched_field} "
        f"{suggestion.matched_text!r})",
    )
