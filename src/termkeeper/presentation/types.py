"""Shared types used by presentation adapters."""

import argparse
from collections.abc import Callable, Mapping

from termkeeper.application import TermKeeperService
from termkeeper.domain import AddResult, InboxItem, Meaning

type CommandResult = AddResult | Meaning | list[InboxItem] | list[Meaning] | Mapping[str, str | int]
type CommandHandler = Callable[[argparse.Namespace, TermKeeperService], CommandResult]
