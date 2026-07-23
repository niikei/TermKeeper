"""Shared types used by CLI presentation components."""

import argparse
from collections.abc import Callable, Mapping

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    CaptureResult,
    ImportResult,
    Meaning,
    MergeResult,
    OccurrenceItem,
    ReferenceLink,
    SearchHit,
    SearchResult,
    StatsSummary,
    TagSummary,
)

type CommandResult = (
    CaptureResult
    | ImportResult
    | Meaning
    | MergeResult
    | OccurrenceItem
    | ReferenceLink
    | SearchResult
    | StatsSummary
    | list[Meaning]
    | list[OccurrenceItem]
    | list[ReferenceLink]
    | list[SearchHit]
    | list[TagSummary]
    | Mapping[str, str | int]
)
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]
