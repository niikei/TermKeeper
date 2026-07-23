import argparse
import csv

from termkeeper.db import (
    add_inbox,
    list_inbox,
    init_db,
    get_inbox,
    create_meaning,
    add_term,
    close_inbox,
    search_term,
    find_registered_term,
    find_open_inbox,
    discard_inbox,
    list_history,
    get_meaning,
    get_terms_by_meaning,
    meaning_exists,
    list_meanings_for_export,
    update_meaning,
    list_meanings,
)


def split_terms(value: str) -> list:
    if not value:
        return []

    terms = []

    for item in value.split(";"):
        item = item.strip()

        if item:
            terms.append(item)

    return terms


def main():
    parser = argparse.ArgumentParser(
        prog="tk",
        description="TermKeeper CLI",
    )

    sub = parser.add_subparsers(dest="command")

    # tk init
    sub.add_parser(
        "init",
        help="Initialize database",
    )

    # tk add <keyword>
    p_add = sub.add_parser(
        "add",
        help="Add term to inbox",
    )
    p_add.add_argument(
        "keyword",
        help="Keyword to add",
    )

    # tk resolve
    p_resolve = sub.add_parser(
        "resolve",
        help="Resolve inbox item",
    )

    p_resolve.add_argument(
        "inbox_id",
        type=int,
    )

    # tk inbox
    sub.add_parser(
        "inbox",
        help="Show inbox items",
    )

    # tk search
    p_search = sub.add_parser(
        "search",
        help="Search term",
    )

    p_search.add_argument(
        "keyword",
    )

    # tk discard
    p_discard = sub.add_parser(
        "discard",
        help="Discard inbox item",
    )

    p_discard.add_argument(
        "inbox_id",
        type=int,
    )

    # tk history
    sub.add_parser(
        "history",
    )

    # tk show
    p_show = sub.add_parser(
        "show",
        help="Show meaning details",
    )

    p_show.add_argument(
        "meaning_id",
        type=int,
    )

    # tk alias
    p_alias = sub.add_parser(
        "alias",
        help="Add alias to meaning",
    )

    p_alias.add_argument(
        "meaning_id",
        type=int,
    )

    p_alias.add_argument(
        "keyword",
    )

    # tk export
    p_export = sub.add_parser(
        "export",
        help="Export meanings to CSV",
    )

    p_export.add_argument(
        "path",
        nargs="?",
        default="termkeeper_export.csv",
    )

    # tk import
    p_import = sub.add_parser(
        "import",
        help="Import meanings from CSV",
    )

    p_import.add_argument(
        "path",
    )

    # tk edit
    p_edit = sub.add_parser(
        "edit",
        help="Edit meaning",
    )

    p_edit.add_argument(
        "meaning_id",
        type=int,
    )

    # tk meanings
    sub.add_parser(
        "meanings",
        help="Show meanings list",
    )

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Database initialized.")
        return

    if args.command == "add":
        registered = find_registered_term(args.keyword)

        if registered:
            print()
            print("Already registered")
            print()

            print(f"[MeaningID={registered['meaning_id']}]")
            print(registered["full_name"])

            if registered["description"]:
                print(registered["description"])

            return

        inbox = find_open_inbox(args.keyword)

        if inbox:
            print()
            print("Already exists in inbox")
            print()

            print(f"InboxID={inbox['inbox_id']}")
            print(f"Keyword={inbox['keyword']}")
            print(f"Status={inbox['status']}")

            return

        inbox_id = add_inbox(args.keyword)

        print(f"Added: InboxID={inbox_id} Keyword={args.keyword}")

        return

    if args.command == "inbox":
        rows = list_inbox()

        if not rows:
            print("Inbox is empty.")
            return

        print()

        for inbox_id, keyword, status, created_at in rows:
            print(f"{inbox_id:>4}  {keyword:<20}  {status:<10}  {created_at}")

        return

    if args.command == "resolve":
        inbox = get_inbox(args.inbox_id)

        if not inbox:
            print("Inbox not found.")
            return

        print()
        print(f"Keyword: {inbox['keyword']}")
        print()

        full_name = input("Full Name: ").strip()
        description = input("Description: ").strip()

        meaning_id = create_meaning(
            full_name,
            description,
        )

        add_term(
            meaning_id,
            inbox["keyword"],
        )

        add_term(
            meaning_id,
            full_name,
        )

        close_inbox(
            args.inbox_id,
            meaning_id,
        )

        print()
        print(f"Created MeaningID={meaning_id}")

        return

    if args.command == "search":
        rows = search_term(args.keyword)

        if not rows:
            print("No results.")
            return

        print()
        print(f"{len(rows)} matches")
        print()

        for row in rows:
            print(
                f"[MeaningID={row['meaning_id']}] "
                f"(Aliases: {row['term_count']})"
            )

            print(row["full_name"])

            if row["description"]:
                print(row["description"])

            print()

        return

    if args.command == "discard":
        count = discard_inbox(args.inbox_id)

        if count == 0:
            print("Inbox not found or already closed.")
            return

        print(f"Discarded: InboxID={args.inbox_id}")

        return

    if args.command == "history":
        rows = list_history()

        if not rows:
            print("History is empty.")
            return

        print()

        for inbox_id, keyword, status, created_at in rows:
            print(f"{inbox_id:>4}  {keyword:<20}  {status:<12}  {created_at}")

        return

    if args.command == "show":
        meaning = get_meaning(args.meaning_id)

        if not meaning:
            print("Meaning not found.")
            return

        terms = get_terms_by_meaning(args.meaning_id)

        print()
        print(f"MeaningID: {meaning['meaning_id']}")
        print()

        print(meaning["full_name"])

        if meaning["description"]:
            print()
            print(meaning["description"])

        print()
        print("Terms")
        print("-----")

        for term in terms:
            print(f"- {term['keyword']}")

        return

    if args.command == "alias":
        if not meaning_exists(args.meaning_id):
            print("Meaning not found.")
            return

        add_term(
            args.meaning_id,
            args.keyword,
        )

        print()

        print(f"Added alias '{args.keyword}'")

        print(f"to MeaningID={args.meaning_id}")

        return

    if args.command == "export":
        rows = list_meanings_for_export()

        with open(
            args.path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "meaning_id",
                    "full_name",
                    "description",
                    "terms",
                ],
            )

            writer.writeheader()

            for row in rows:
                writer.writerow(
                    {
                        "meaning_id": row["meaning_id"],
                        "full_name": row["full_name"],
                        "description": row["description"] or "",
                        "terms": row["terms"] or "",
                    }
                )

        print(f"Exported: {args.path}")

        return

    if args.command == "import":
        imported_count = 0
        updated_count = 0

        with open(
            args.path,
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            reader = csv.DictReader(f)

            for row in reader:
                meaning_id_text = (row.get("meaning_id") or "").strip()

                full_name = (row.get("full_name") or "").strip()

                description = (row.get("description") or "").strip()

                terms = split_terms(row.get("terms") or "")

                if not full_name:
                    continue

                if meaning_id_text:
                    meaning_id = int(meaning_id_text)

                    if meaning_exists(meaning_id):
                        update_meaning(
                            meaning_id,
                            full_name,
                            description,
                        )

                        updated_count += 1

                    else:
                        meaning_id = create_meaning(
                            full_name,
                            description,
                        )

                        imported_count += 1

                else:
                    meaning_id = create_meaning(
                        full_name,
                        description,
                    )

                    imported_count += 1

                add_term(
                    meaning_id,
                    full_name,
                )

                for term in terms:
                    add_term(
                        meaning_id,
                        term,
                    )

        print(f"Imported: {imported_count}")

        print(f"Updated : {updated_count}")

        return

    if args.command == "edit":
        meaning = get_meaning(args.meaning_id)

        if not meaning:
            print("Meaning not found.")
            return

        print()
        print(f"MeaningID: {meaning['meaning_id']}")
        print()

        print(f"Current Full Name: {meaning['full_name']}")

        new_full_name = input("New Full Name (blank to keep): ").strip()

        print()
        print("Current Description:")
        print(meaning["description"] or "")

        new_description = input("New Description (blank to keep): ").strip()

        full_name = new_full_name if new_full_name else meaning["full_name"]

        description = new_description if new_description else meaning["description"]

        update_meaning(
            args.meaning_id,
            full_name,
            description,
        )

        add_term(
            args.meaning_id,
            full_name,
        )

        print()
        print(f"Updated MeaningID={args.meaning_id}")

        return

    if args.command == "meanings":
        rows = list_meanings()

        if not rows:
            print("No meanings.")
            return

        print()

        print(f"{'ID':<4}  {'Alias':<5}  {'Full Name':<35}  Description")

        print("-" * 120)

        for row in rows:
            description = row["description"] or ""

            if len(description) > 40:
                description = description[:40] + "..."

            print(
                f"{row['meaning_id']:<4}  "
                f"{row['term_count']:<5}  "
                f"{row['full_name']:<35}  "
                f"{description}"
            )

        return

    parser.print_help()


if __name__ == "__main__":
    main()
