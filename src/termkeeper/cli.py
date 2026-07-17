import argparse

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
)


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

        for row in rows:
            print(f"[MeaningID={row['meaning_id']}]")
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
            print(
                f"{inbox_id:>4}  "
                f"{keyword:<20}  "
                f"{status:<12}  "
                f"{created_at}"
            )

        return
    
    if args.command == "show":

        meaning = get_meaning(
            args.meaning_id
        )

        if not meaning:
            print("Meaning not found.")
            return

        terms = get_terms_by_meaning(
            args.meaning_id
        )

        print()
        print(
            f"MeaningID: {meaning['meaning_id']}"
        )
        print()

        print(
            meaning["full_name"]
        )

        if meaning["description"]:
            print()
            print(
                meaning["description"]
            )

        print()
        print("Terms")
        print("-----")

        for term in terms:
            print(
                f"- {term['keyword']}"
            )

        return

    parser.print_help()


if __name__ == "__main__":
    main()
