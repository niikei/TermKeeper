"""One command handler per CLI use case."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import AddResult, InboxItem, Meaning
from termkeeper.presentation.csv_io import export_meanings, import_meanings
from termkeeper.presentation.rendering import print_inbox, print_meaning
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


def handle_search(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.search(args.keyword)
    if not args.json:
        print(f"{len(result)} match(es)")
        for item in result:
            print_meaning(item)
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
    result = service.meanings()
    if not args.json:
        for item in result:
            print_meaning(item)
    return result


def handle_export(
    args: argparse.Namespace,
    _service: TermKeeperService,
) -> dict[str, str | int]:
    count = export_meanings(args.path)
    if not args.json:
        print(f"Exported {count} meaning(s) to {args.path}.")
    return {"exported": count, "path": args.path}


def handle_import(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    result = import_meanings(args.path, service)
    if not args.json:
        print(
            f"Created {result['created']}, updated {result['updated']}, "
            f"skipped {result['skipped']}.",
        )
    return result


HANDLERS: dict[str, CommandHandler] = {
    "init": handle_init,
    "add": handle_add,
    "inbox": handle_inbox,
    "history": handle_history,
    "resolve": handle_resolve,
    "search": handle_search,
    "discard": handle_discard,
    "show": handle_show,
    "alias": handle_alias,
    "edit": handle_edit,
    "meanings": handle_meanings,
    "export": handle_export,
    "import": handle_import,
}
