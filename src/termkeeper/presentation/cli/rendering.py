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
from termkeeper.presentation.cli.style import (
    BOLD,
    CYAN,
    UNDERLINE,
    command,
    danger,
    heading,
    identifier,
    muted,
    scope_label,
    status_label,
    styled,
    warning,
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


def print_meaning_candidates(
    candidates: Sequence[Meaning],
    *,
    heading: str,
) -> None:
    """Print distinguishable meaning choices with their scopes."""
    print(styled(heading, BOLD))
    for candidate in candidates:
        meaning_id = identifier(f"#{candidate.meaning_id}")
        scope = scope_label(f"[{candidate.scope}]")
        print(f"  {meaning_id} {scope} {candidate.full_name}")


def _print_json_value(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def print_inbox(items: Sequence[OccurrenceItem]) -> None:
    if not items:
        print(muted("Inbox is empty."))
        return
    print(heading(f"{'ID':>4}  {'Term':<24} {'Source':<16} Occurred (UTC)"))
    for item in items:
        item_id = identifier(f"{item.occurrence_id:>4}")
        term = styled(f"{item.keyword:<24.24}", BOLD)
        source = muted(f"{(item.source or '-'):<16.16}")
        occurred_at = muted(str(item.occurred_at))
        print(
            f"{item_id}  {term} {source} {occurred_at}",
        )
        details = " / ".join(value for value in (item.memo, item.source) if value)
        if details:
            print(muted(f"      {details}"))


def print_occurrences(items: Sequence[OccurrenceItem]) -> None:
    if not items:
        print(muted("No occurrences found."))
        return
    print(heading(f"{'ID':>4}  {'Term':<24} {'Source':<16} Occurred (UTC)"))
    for item in items:
        item_id = identifier(f"{item.occurrence_id:>4}")
        term = styled(f"{item.keyword:<24.24}", BOLD)
        source = muted(f"{(item.source or '-'):<16.16}")
        occurred_at = muted(str(item.occurred_at))
        print(f"{item_id}  {term} {source} {occurred_at}")
        details = [f"memo: {item.memo}"] if item.memo else []
        details.append(f"status: {status_label(item.status)}")
        if item.meaning_id is not None:
            details.append(f"meaning: {identifier(str(item.meaning_id))}")
        if details:
            print("      " + " / ".join(details))


def print_has_more(result: Page[OccurrenceItem]) -> None:
    if result.has_more:
        next_offset = result.offset + len(result.items)
        next_command = command(f"--offset {next_offset}")
        print(f"More items are available. Continue with {next_command}.")


def print_stats(stats: StatsSummary) -> None:
    pending = warning(str(stats.pending_occurrences))
    print(
        f"Occurrences: {stats.total_occurrences}  Pending: {pending}  "
        f"Meanings: {stats.active_meanings}",
    )
    print(heading("Top terms:"))
    for item in stats.top_terms:
        last_seen = muted(f"(last seen: {item.last_seen_at})")
        print(f"  {item.value}: {item.count} {last_seen}")
    print(heading("Top sources:"))
    for item in stats.top_sources:
        last_seen = muted(f"(last seen: {item.last_seen_at})")
        print(f"  {item.value}: {item.count} {last_seen}")


def print_references(items: list[ReferenceLink]) -> None:
    for item in items:
        label = item.title or item.url
        print(f"{identifier(f'[{item.reference_id}]')} {label}")
        if item.title:
            print(f"    {styled(item.url, UNDERLINE, CYAN)}")


def print_meaning(item: Meaning) -> None:
    marker = warning("★ ") if item.is_favorite else ""
    meaning_id = identifier(f"[{item.meaning_id}]")
    name = heading(item.full_name)
    scope = scope_label(f"[{item.scope}]")
    print(f"{meaning_id} {marker}{name} {scope}")
    if item.description:
        print(item.description)
    if item.terms:
        print("Aliases: " + ", ".join(item.terms))
    if item.tags:
        print("Tags: " + ", ".join(command(tag) for tag in item.tags))
    if item.deleted_at:
        print(danger(f"Deleted: {item.deleted_at}"))
    print(muted(f"Created: {item.created_at}  Updated: {item.updated_at}"))


def print_search_hit(hit: SearchHit) -> None:
    marker = warning("★ ") if hit.meaning.is_favorite else ""
    meaning_id = identifier(f"[{hit.meaning.meaning_id}]")
    name = heading(hit.meaning.full_name)
    scope = scope_label(f"[{hit.meaning.scope}]")
    print(f"{meaning_id} {marker}{name} {scope}")
    match = styled(repr(hit.matched_text), BOLD)
    score = muted(f"score {hit.score}")
    print(f"    {hit.matched_field}: {match} · {score}")


def print_search_suggestion(suggestion: SearchSuggestion) -> None:
    meaning_id = identifier(f"[{suggestion.meaning.meaning_id}]")
    scope = scope_label(f"[{suggestion.meaning.scope}]")
    detail = muted(
        f"({suggestion.similarity}% via {suggestion.matched_field} "
        f"{suggestion.matched_text!r})",
    )
    print(
        f"  {meaning_id} {suggestion.meaning.full_name} {scope} {detail}",
    )
