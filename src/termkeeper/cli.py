"""Command-line adapter for TermKeeper."""

import argparse
import csv
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from termkeeper import db
from termkeeper.models import AddResult, InboxItem, Meaning
from termkeeper.service import NotFoundError, TermKeeperService, ValidationError

type CommandResult = AddResult | Meaning | list[InboxItem] | list[Meaning] | Mapping[str, str | int]
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]


def split_terms(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tk", description="Capture now, understand later.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize or migrate the database")

    add = sub.add_parser("add", help="Add a term to the inbox")
    add.add_argument("keyword")
    add.add_argument("--memo", help="Context or a short reminder")
    add.add_argument("--source", help="Where the term was encountered")

    sub.add_parser("inbox", help="Show unresolved items")
    sub.add_parser("history", help="Show all captured items")

    resolve = sub.add_parser("resolve", help="Turn an inbox item into a meaning")
    resolve.add_argument("inbox_id", type=int)
    resolve.add_argument("--name", help="Full name (omit for an interactive prompt)")
    resolve.add_argument("--description", help="Description")

    search = sub.add_parser("search", help="Search terms and descriptions")
    search.add_argument("keyword")

    discard = sub.add_parser("discard", help="Discard an inbox item")
    discard.add_argument("inbox_id", type=int)

    show = sub.add_parser("show", help="Show a meaning")
    show.add_argument("meaning_id", type=int)

    alias = sub.add_parser("alias", help="Add an alias to a meaning")
    alias.add_argument("meaning_id", type=int)
    alias.add_argument("keyword")

    edit = sub.add_parser("edit", help="Edit a meaning")
    edit.add_argument("meaning_id", type=int)
    edit.add_argument("--name", help="New full name")
    edit.add_argument("--description", help="New description")

    sub.add_parser("meanings", help="List meanings")
    export = sub.add_parser("export", help="Export meanings to CSV")
    export.add_argument("path", nargs="?", default="termkeeper_export.csv")
    import_ = sub.add_parser("import", help="Import meanings from CSV")
    import_.add_argument("path")
    return parser


def _json(value: CommandResult) -> None:
    if isinstance(value, (AddResult, Meaning)):
        payload = value.to_dict()
    elif isinstance(value, list):
        payload = [item.to_dict() for item in value]
    else:
        payload = dict(value)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _print_inbox(items: list[InboxItem]) -> None:
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


def _print_meaning(item: Meaning) -> None:
    print(f"[{item.meaning_id}] {item.full_name}")
    if item.description:
        print(item.description)
    if item.terms:
        print("Aliases: " + ", ".join(item.terms))
    print(f"Created: {item.created_at}  Updated: {item.updated_at}")


def _export(path: str) -> int:
    rows = db.list_meanings_for_export()
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["meaning_id", "full_name", "description", "terms", "created_at", "updated_at"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] or "" for field in fields})
    return len(rows)


def _import(path: str, service: TermKeeperService) -> dict[str, int]:
    created = updated = skipped = 0
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("full_name") or "").strip()
            if not name:
                skipped += 1
                continue
            description = (row.get("description") or "").strip() or None
            id_text = (row.get("meaning_id") or "").strip()
            if id_text and db.meaning_exists(int(id_text)):
                meaning = service.edit(int(id_text), name, description)
                updated += 1
            else:
                meaning_id = db.create_meaning(name, description)
                db.add_term(meaning_id, name)
                meaning = service.get_meaning(meaning_id)
                created += 1
            for term in split_terms(row.get("terms") or ""):
                service.add_alias(meaning.meaning_id, term)
    return {"created": created, "updated": updated, "skipped": skipped}


def _handle_init(args: argparse.Namespace, _service: TermKeeperService) -> dict[str, str]:
    if not args.json:
        print("Database initialized and up to date.")
    return {"status": "ok"}


def _handle_add(args: argparse.Namespace, service: TermKeeperService) -> AddResult:
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


def _handle_inbox(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.inbox()
    if not args.json:
        _print_inbox(result)
    return result


def _handle_history(args: argparse.Namespace, service: TermKeeperService) -> list[InboxItem]:
    result = service.history()
    if not args.json:
        _print_inbox(result)
    return result


def _handle_resolve(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
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


def _handle_search(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.search(args.keyword)
    if not args.json:
        print(f"{len(result)} match(es)")
        for item in result:
            _print_meaning(item)
    return result


def _handle_discard(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    service.discard(args.inbox_id)
    if not args.json:
        print(f"Discarded inbox #{args.inbox_id}.")
    return {"discarded": args.inbox_id}


def _handle_show(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.get_meaning(args.meaning_id)
    if not args.json:
        _print_meaning(result)
    return result


def _handle_alias(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_alias(args.meaning_id, args.keyword)
    if not args.json:
        print(f"Added alias '{args.keyword}' to meaning #{args.meaning_id}.")
    return result


def _handle_edit(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
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


def _handle_meanings(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.meanings()
    if not args.json:
        for item in result:
            _print_meaning(item)
    return result


def _handle_export(
    args: argparse.Namespace,
    _service: TermKeeperService,
) -> dict[str, str | int]:
    count = _export(args.path)
    if not args.json:
        print(f"Exported {count} meaning(s) to {args.path}.")
    return {"exported": count, "path": args.path}


def _handle_import(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    result = _import(args.path, service)
    if not args.json:
        print(
            f"Created {result['created']}, updated {result['updated']}, "
            f"skipped {result['skipped']}.",
        )
    return result


HANDLERS: dict[str, CommandHandler] = {
    "init": _handle_init,
    "add": _handle_add,
    "inbox": _handle_inbox,
    "history": _handle_history,
    "resolve": _handle_resolve,
    "search": _handle_search,
    "discard": _handle_discard,
    "show": _handle_show,
    "alias": _handle_alias,
    "edit": _handle_edit,
    "meanings": _handle_meanings,
    "export": _handle_export,
    "import": _handle_import,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = TermKeeperService()
    service.initialize()
    try:
        result = HANDLERS[args.command](args, service)
    except (ValidationError, NotFoundError, ValueError, OSError) as exc:
        if args.json:
            _json({"error": type(exc).__name__, "message": str(exc)})
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    else:
        if args.json:
            _json(result)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
