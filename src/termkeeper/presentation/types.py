"""Shared types used by presentation adapters."""

import argparse
from collections.abc import Callable, Mapping

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    AddResult,
    ImportResult,
    InboxItem,
    Meaning,
    MergeResult,
    OccurrenceItem,
    SearchHit,
    SearchResult,
    TagSummary,
)

type CommandResult = (
    AddResult
    | ImportResult
    | Meaning
    | MergeResult
    | SearchResult
    | list[InboxItem]
    | list[Meaning]
    | list[OccurrenceItem]
    | list[SearchHit]
    | list[TagSummary]
    | Mapping[str, str | int]
)
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]
