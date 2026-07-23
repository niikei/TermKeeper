"""Configuration command handlers."""

import argparse

from termkeeper.application import TermKeeperService


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
            if result:
                for key, value in result.items():
                    print(f"{key}={value}")
            else:
                print("No configuration is set.")
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
