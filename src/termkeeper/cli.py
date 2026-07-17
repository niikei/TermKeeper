import argparse

from termkeeper.db import (
    add_inbox,
    init_db,
    list_inbox,
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

    # tk inbox
    sub.add_parser(
        "inbox",
        help="Show inbox items",
    )

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Database initialized.")
        return

    if args.command == "add":
        inbox_id = add_inbox(args.keyword)

        print(
            f"Added: InboxID={inbox_id} "
            f"Keyword={args.keyword}"
        )
        return

    if args.command == "inbox":
        rows = list_inbox()

        if not rows:
            print("Inbox is empty.")
            return

        print()

        for inbox_id, keyword, status, created_at in rows:
            print(
                f"{inbox_id:>4}  "
                f"{keyword:<20}  "
                f"{status:<10}  "
                f"{created_at}"
            )

        return

    parser.print_help()


if __name__ == "__main__":
    main()
