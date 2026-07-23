"""One command handler per CLI use case."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    AddResult,
    ImportResult,
    InboxItem,
    Meaning,
    MergeResult,
    OccurrenceItem,
    OccurrenceQuery,
    OccurrenceUpdate,
    SearchQuery,
    SearchResult,
    TagSummary,
)
from termkeeper.presentation.csv_io import export_meanings, import_meanings
from termkeeper.presentation.rendering import (
    print_inbox,
    print_meaning,
    print_occurrences,
    print_search_hit,
    print_search_suggestion,
)
from termkeeper.presentation.types import CommandHandler


def handle_init(args: argparse.Namespace, _service: TermKeeperService) -> dict[str, str]:
    if not args.json:
        print("Database initialized and up to date.")
    return {"status": "ok"}


def handle_add(args: argparse.Namespace, service: TermKeeperService) -> AddResult:
    result = service.add(args.keyword, args.memo, args.source)
    if args.json:
        return result
    if result.inbox is not None:
        if result.outcome == "created":
            print(f"Added inbox #{result.inbox.inbox_id}: {result.inbox.keyword}")
        else:
            print(
                f"Already in inbox #{result.inbox.inbox_id}; "
                f"seen count is now {result.inbox.occurrence_count}.",
            )
    elif result.meaning is not None:
        print(
            f"Already registered as meaning #{result.meaning.meaning_id}: "
            f"{result.meaning.full_name}",
        )
    return result


def handle_inbox(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.inbox()
    if not args.json:
        print_inbox(result)
    return result


def handle_history(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.history()
    if not args.json:
        print_inbox(result)
    return result


def handle_inbox_edit(args: argparse.Namespace, service: TermKeeperService) -> InboxItem:
    result = service.edit_inbox(args.inbox_id, args.keyword)
    if not args.json:
        print(f"Updated inbox #{args.inbox_id}: {result.keyword}")
    return result


def handle_occurrences(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> list[OccurrenceItem]:
    query = OccurrenceQuery(
        meaning_id=args.meaning_id,
        inbox_id=args.inbox_id,
        keyword=args.keyword,
        source=args.source,
        since=args.since,
        limit=args.limit,
    )
    result = service.occurrences(query)
    if not args.json:
        print_occurrences(result)
    return result


def handle_occurrence_edit(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> OccurrenceItem:
    update = OccurrenceUpdate(
        keyword=args.keyword,
        memo=args.memo,
        source=args.source,
        clear_memo=args.clear_memo,
        clear_source=args.clear_source,
    )
    result = service.edit_occurrence(args.occurrence_id, update)
    if not args.json:
        print(f"Updated occurrence #{args.occurrence_id}.")
    return result


def handle_resolve(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    name = args.name
    description = args.description
    if name is None:
        item = service.get_inbox(args.inbox_id)
        print(f"Resolving: {item.keyword}")
        name = input("Full name: ").strip()
        if description is None:
            description = input("Description: ").strip() or None
    result = service.resolve(args.inbox_id, name, description)
    if not args.json:
        print(f"Created meaning #{result.meaning_id}: {result.full_name}")
    return result


def handle_search(args: argparse.Namespace, service: TermKeeperService) -> SearchResult:
    query = SearchQuery(
        text=args.keyword,
        match_all=args.match_all,
        field=args.search_field,
        limit=args.limit,
        tag=args.tag,
        suggestion_limit=args.suggestion_limit,
    )
    result = service.search(query)
    if not args.json:
        print(f"{len(result.hits)} match(es)")
        for item in result.hits:
            print_search_hit(item)
        if result.suggestions:
            print("Did you mean:")
            for suggestion in result.suggestions:
                print_search_suggestion(suggestion)
    return result


def handle_discard(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.discard(args.inbox_id)
    if not args.json:
        print(f"Discarded inbox #{args.inbox_id}.")
    return {"discarded": args.inbox_id}


def handle_show(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.get_meaning(args.meaning_id)
    if not args.json:
        print_meaning(result)
    return result


def handle_alias(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_alias(args.meaning_id, args.keyword)
    if not args.json:
        print(f"Added alias '{args.keyword}' to meaning #{args.meaning_id}.")
    return result


def handle_unalias(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.remove_alias(args.meaning_id, args.keyword)
    if not args.json:
        print(f"Removed alias '{args.keyword}' from meaning #{args.meaning_id}.")
    return result


def handle_delete(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.delete_meaning(args.meaning_id)
    if not args.json:
        print(f"Moved meaning #{args.meaning_id} to trash.")
    return {"deleted": args.meaning_id}


def handle_trash(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.trash()
    if not args.json:
        for item in result:
            print_meaning(item)
    return result


def handle_restore(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.restore_meaning(args.meaning_id)
    if not args.json:
        print(f"Restored meaning #{args.meaning_id}.")
    return result


def handle_purge(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.purge_meaning(args.meaning_id)
    if not args.json:
        print(f"Permanently deleted meaning #{args.meaning_id}.")
    return {"purged": args.meaning_id}


def handle_merge(args: argparse.Namespace, service: TermKeeperService) -> MergeResult:
    result = service.merge_meanings(args.source_id, args.target_id, dry_run=args.dry_run)
    if not args.json:
        action = "Would merge" if args.dry_run else "Merged"
        print(
            f"{action} meaning #{args.source_id} into #{args.target_id}: "
            f"{result.terms_moved} term(s), {result.tags_moved} tag(s), "
            f"{result.occurrences_moved} occurrence(s), {result.inboxes_moved} inbox(es).",
        )
    return result


def handle_tag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_tag(args.meaning_id, args.name)
    if not args.json:
        print(f"Tagged meaning #{args.meaning_id} with '{args.name}'.")
    return result


def handle_untag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.remove_tag(args.meaning_id, args.name)
    if not args.json:
        print(f"Removed tag '{args.name}' from meaning #{args.meaning_id}.")
    return result


def handle_tags(args: argparse.Namespace, service: TermKeeperService) -> list[TagSummary]:
    result = service.tags()
    if not args.json:
        for tag in result:
            print(f"{tag.name} ({tag.meaning_count})")
    return result


def handle_edit(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    current = service.get_meaning(args.meaning_id)
    name = args.name
    description = args.description
    if name is None:
        name = input(f"Full name [{current.full_name}]: ").strip() or current.full_name
        if description is None:
            entered = input(f"Description [{current.description or ''}]: ").strip()
            description = entered or current.description
    result = service.edit(args.meaning_id, name, description)
    if not args.json:
        print(f"Updated meaning #{args.meaning_id}.")
    return result


def handle_meanings(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.meanings(args.tag)
    if not args.json:
        for item in result:
            print_meaning(item)
    return result


def handle_config(args: argparse.Namespace, service: TermKeeperService) -> dict[str, str]:
    if args.unset:
        if args.key is None:
            message = "config --unset requires a key"
            raise ValueError(message)
        result = service.unset_config(args.key)
        if not args.json:
            print(f"Unset {args.key}.")
        return result
    if args.list_config or args.key is None:
        result = service.list_config()
        if not args.json:
            for key, value in result.items():
                print(f"{key}={value}")
        return result
    if args.value is None:
        setting = service.get_config(args.key)
        if not args.json:
            print(setting["value"])
        return setting
    result = service.set_config(args.key, args.value)
    if not args.json:
        print(f"Set {args.key}.")
    return result


def handle_export(
    args: argparse.Namespace,
    _service: TermKeeperService,
) -> dict[str, str | int]:
    count = export_meanings(args.path, _service)
    if not args.json:
        print(f"Exported {count} meaning(s) to {args.path}.")
    return {"exported": count, "path": args.path}


def handle_import(args: argparse.Namespace, service: TermKeeperService) -> ImportResult:
    result = import_meanings(
        args.path,
        service,
        dry_run=args.dry_run,
        strict=args.strict,
    )
    if not args.json:
        action = "Would create" if result.dry_run else "Created"
        print(
            f"{action} {result.created}, updated {result.updated}, skipped {result.skipped}.",
        )
        for issue in result.issues:
            print(f"Row {issue.row_number}: {issue.message}")
    return result


HANDLERS: dict[str, CommandHandler] = {
    "init": handle_init,
    "add": handle_add,
    "inbox": handle_inbox,
    "history": handle_history,
    "inbox-edit": handle_inbox_edit,
    "occurrences": handle_occurrences,
    "occurrence-edit": handle_occurrence_edit,
    "resolve": handle_resolve,
    "search": handle_search,
    "discard": handle_discard,
    "show": handle_show,
    "alias": handle_alias,
    "unalias": handle_unalias,
    "delete": handle_delete,
    "trash": handle_trash,
    "restore": handle_restore,
    "purge": handle_purge,
    "merge": handle_merge,
    "tag": handle_tag,
    "untag": handle_untag,
    "tags": handle_tags,
    "edit": handle_edit,
    "meanings": handle_meanings,
    "config": handle_config,
    "export": handle_export,
    "import": handle_import,
}
