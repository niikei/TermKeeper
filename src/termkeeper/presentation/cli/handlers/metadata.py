"""Meaning metadata command handlers."""

import argparse

from termkeeper.application import TermKeeperService
from termkeeper.domain import Meaning, ReferenceLink, ReferenceUpdate, TagSummary
from termkeeper.presentation.cli.rendering import print_meaning, print_references


def handle_tag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.add_tag(args.meaning_id, args.name)
    if not args.json:
        print(f"Tagged meaning #{args.meaning_id} with '{args.name}'.")
    return result


def handle_untag(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.remove_tag(args.meaning_id, args.name)
    if not args.json:
        print(f"Removed tag '{args.name}' from meaning #{args.meaning_id}.")
    return result


def handle_tags(args: argparse.Namespace, service: TermKeeperService) -> list[TagSummary]:
    result = service.tags()
    if not args.json:
        if result:
            for tag in result:
                print(f"{tag.name} ({tag.meaning_count})")
        else:
            print("No tags found.")
    return result


def handle_favorite(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.favorite_meaning(args.meaning_id)
    if not args.json:
        print(f"Favorited meaning #{args.meaning_id}.")
    return result


def handle_unfavorite(args: argparse.Namespace, service: TermKeeperService) -> Meaning:
    result = service.unfavorite_meaning(args.meaning_id)
    if not args.json:
        print(f"Unfavorited meaning #{args.meaning_id}.")
    return result


def handle_relate(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.relate(args.meaning_id, args.related_id)
    if not args.json:
        print(f"Related meaning #{args.meaning_id} to #{args.related_id}.")
    return result


def handle_unrelate(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.unrelate(args.meaning_id, args.related_id)
    if not args.json:
        print(f"Unrelated meaning #{args.meaning_id} from #{args.related_id}.")
    return result


def handle_related(args: argparse.Namespace, service: TermKeeperService) -> list[Meaning]:
    result = service.related(args.meaning_id)
    if not args.json:
        if result:
            for item in result:
                print_meaning(item)
        else:
            print("No related meanings found.")
    return result


def handle_reference_add(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> ReferenceLink:
    result = service.add_reference(args.meaning_id, args.url, args.title)
    if not args.json:
        print(f"Added reference #{result.reference_id} to meaning #{args.meaning_id}.")
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
        print(f"Updated reference #{args.reference_id}.")
    return result


def handle_reference_remove(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> ReferenceLink:
    result = service.remove_reference(args.reference_id)
    if not args.json:
        print(f"Removed reference #{args.reference_id}.")
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
            print("No references found.")
    return result
