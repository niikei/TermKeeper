"""Shared types used by presentation adapters."""

import argparse
from collections.abc import Callable, Mapping

from termkeeper.application import TermKeeperService
from termkeeper.domain import AddResult, InboxItem, Meaning, MergeResult, OccurrenceItem, SearchHit

type CommandResult = (
    AddResult
    | Meaning
    | MergeResult
    | list[InboxItem]
    | list[Meaning]
    | list[OccurrenceItem]
    | list[SearchHit]
    | Mapping[str, str | int]
)
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]
