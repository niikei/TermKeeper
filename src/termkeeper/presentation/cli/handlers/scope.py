"""Meaning scope command handlers."""

import argparse

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import Scope
from termkeeper.presentation.cli.handlers.common import confirm_destructive


def handle_scope_add(args: argparse.Namespace, service: TermKeeperService) -> Scope:
    result = service.create_scope(args.name, args.description)
    if not args.json:
        print(f"Created scope #{result.scope_id}: {result.name}")
    return result


def handle_scopes(args: argparse.Namespace, service: TermKeeperService) -> list[Scope]:
    result = service.scopes()
    if not args.json:
        for scope in result:
            print(f"#{scope.scope_id} {scope.name}")
    return result


def handle_scope_edit(args: argparse.Namespace, service: TermKeeperService) -> Scope:
    current = service.get_scope(args.scope_id)
    if args.name is None and args.description is None and not args.clear_description:
        message = "At least one of --name, --description, or --clear-description is required."
        raise ValidationError(message)
    result = service.edit_scope(
        args.scope_id,
        args.name if args.name is not None else current.name,
        (
            None
            if args.clear_description
            else args.description if args.description is not None else current.description
        ),
    )
    if not args.json:
        print(f"Updated scope #{args.scope_id}.")
    return result


def handle_scope_delete(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    confirm_destructive(args, f"Delete unused scope #{args.scope_id}?")
    service.delete_scope(args.scope_id)
    if not args.json:
        print(f"Deleted scope #{args.scope_id}.")
    return {"scope_id": args.scope_id}
