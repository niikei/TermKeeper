import argparse

from termkeeper.db import init_db


def main():
    parser = argparse.ArgumentParser(
        prog="tk"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print("Database initialized.")
        return

    parser.print_help()
