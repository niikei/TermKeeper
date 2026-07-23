"""Model Context Protocol adapter package."""

from termkeeper.adapters.mcp.inputs import (
    InboxSearchFilters,
    MeaningFilters,
    OccurrenceFilters,
    OccurrenceSearchFilters,
    ScopeSearchFilters,
    SearchFilters,
)
from termkeeper.adapters.mcp.server import create_server
from termkeeper.adapters.mcp.tools import TermKeeperMcpTools

__all__ = [
    "InboxSearchFilters",
    "MeaningFilters",
    "OccurrenceFilters",
    "OccurrenceSearchFilters",
    "ScopeSearchFilters",
    "SearchFilters",
    "TermKeeperMcpTools",
    "create_server",
]
