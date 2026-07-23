"""Meaning scope command handlers."""

import argparse

from termkeeper.application import TermKeeperService, ValidationError
from termkeeper.domain import Page, Scope
from termkeeper.presentation.cli.handlers.common import confirm_destructive
from termkeeper.presentation.cli.rendering import print_has_more, print_scopes
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
        print_scopes(result)
    return result


def handle_scope_search(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> Page[Scope]:
    result = service.search_scopes(args.text, offset=args.offset, limit=args.limit)
    if not args.json:
        print_scopes(result.items)
        print_has_more(result)
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
