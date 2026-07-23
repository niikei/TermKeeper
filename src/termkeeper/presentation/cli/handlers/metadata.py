"""Meaning metadata command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import Meaning, ReferenceLink, ReferenceUpdate, TagSummary
from termkeeper.presentation.cli.rendering import print_meaning, print_references
from termkeeper.presentation.cli.style import command, identifier, muted, success, warning


def handle_tag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_tag(args.meaning_id, args.name)
    if not args.json:
        print(
            f"{success('Tagged')} meaning {identifier(f'#{args.meaning_id}')} "
            f"with '{command(args.name)}'.",
        )
    return result


def handle_untag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.remove_tag(args.meaning_id, args.name)
    if not args.json:
        print(
            f"{success('Removed')} tag '{command(args.name)}' "
            f"from meaning {identifier(f'#{args.meaning_id}')}.",
        )
    return result


def handle_tags(args: argparse.Namespace, service: TermKeeperService) -> list[TagSummary]:
    result = service.tags()
    if not args.json:
        if result:
            for tag in result:
                print(f"{command(tag.name)} ({tag.meaning_count})")
        else:
            print(muted("No tags found."))
    return result


def handle_favorite(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.favorite_meaning(args.meaning_id)
    if not args.json:
        print(f"{warning('★ Favorited')} meaning {identifier(f'#{args.meaning_id}')}.")
    return result


def handle_unfavorite(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.unfavorite_meaning(args.meaning_id)
    if not args.json:
        print(f"{success('Unfavorited')} meaning {identifier(f'#{args.meaning_id}')}.")
    return result


def handle_relate(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.relate(args.meaning_id, args.related_id)
    if not args.json:
        print(
            f"{success('Related')} meaning {identifier(f'#{args.meaning_id}')} "
            f"to {identifier(f'#{args.related_id}')}.",
        )
    return result


def handle_unrelate(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.unrelate(args.meaning_id, args.related_id)
    if not args.json:
        print(
            f"{success('Unrelated')} meaning {identifier(f'#{args.meaning_id}')} "
            f"from {identifier(f'#{args.related_id}')}.",
        )
    return result


def handle_related(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.related(args.meaning_id)
    if not args.json:
        if result:
            for item in result:
                print_meaning(item)
        else:
            print(muted("No related meanings found."))
    return result


def handle_reference_add(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> ReferenceLink:
    result = service.add_reference(args.meaning_id, args.url, args.title)
    if not args.json:
        print(
            f"{success('Added')} reference {identifier(f'#{result.reference_id}')} "
            f"to meaning {identifier(f'#{args.meaning_id}')}.",
        )
    return result


def handle_reference_edit(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> ReferenceLink:
    update = ReferenceUpdate(
        url=args.url,
        title=args.title,
        clear_title=args.clear_title,
    )
    result = service.edit_reference(args.reference_id, update)
    if not args.json:
        print(f"{success('Updated')} reference {identifier(f'#{args.reference_id}')}.")
    return result


def handle_reference_remove(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> ReferenceLink:
    result = service.remove_reference(args.reference_id)
    if not args.json:
        print(f"{success('Removed')} reference {identifier(f'#{args.reference_id}')}.")
    return result


def handle_references(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> list[ReferenceLink]:
    result = service.references(args.meaning_id)
    if not args.json:
        if result:
            print_references(result)
        else:
            print(muted("No references found."))
    return result
