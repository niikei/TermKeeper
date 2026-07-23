"""Meaning scope command handlers."""

import argparse

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import Scope
from termkeeper.presentation.cli.handlers.common import confirm_destructive
from termkeeper.presentation.cli.style import danger, heading, identifier, success


def handle_scope_add(args: argparse.Namespace, service: TermKeeperService) -> Scope:
    result = service.create_scope(args.name, args.description)
    if not args.json:
        print(
            f"{success('Created')} scope {identifier(f'#{result.scope_id}')}: "
            f"{heading(result.name)}",
        )
    return result


def handle_scopes(args: argparse.Namespace, service: TermKeeperService) -> list[Scope]:
    result = service.scopes()
    if not args.json:
        for scope in result:
            print(f"{identifier(f'#{scope.scope_id}')} {heading(scope.name)}")
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
        print(f"{success('Updated')} scope {identifier(f'#{args.scope_id}')}.")
    return result


def handle_scope_delete(args: argparse.Namespace, service: TermKeeperService) -> dict[str, int]:
    confirm_destructive(args, f"Delete unused scope #{args.scope_id}?")
    service.delete_scope(args.scope_id)
    if not args.json:
        print(f"{danger('Deleted')} scope {identifier(f'#{args.scope_id}')}.")
    return {"scope_id": args.scope_id}
