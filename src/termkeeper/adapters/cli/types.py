"""Shared types used by CLI presentation components."""

import argparse
from collections.abc import Callable, Mapping

from termkeeper.application import TermKeeperService
from termkeeper.domain import (
    CaptureBatchResult,
    CaptureResult,
    ImportResult,
    Meaning,
    MergeResult,
    OccurrenceItem,
    Page,
    ReferenceLink,
    Scope,
    SearchHit,
    SearchResult,
    StatsSummary,
    TagSummary,
)

type CommandResult = (
    CaptureBatchResult
    | CaptureResult
    | ImportResult
    | Meaning
    | MergeResult
    | OccurrenceItem
    | Page[OccurrenceItem]
    | Page[Meaning]
    | Page[Scope]
    | ReferenceLink
    | SearchResult
    | Scope
    | StatsSummary
    | list[Meaning]
    | list[OccurrenceItem]
    | list[ReferenceLink]
    | list[SearchHit]
    | list[Scope]
    | list[TagSummary]
    | Mapping[str, str | int]
)
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]
