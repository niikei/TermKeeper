"""Model Context Protocol adapter package."""

from termkeeper.adapters.mcp.inputs import (
    CaptureBatchInput,
    CaptureTermInput,
    InboxSearchFilters,
    MeaningCreateInput,
    MeaningEditInput,
    MeaningFilters,
    OccurrenceFilters,
    OccurrenceSearchFilters,
    ScopeSearchFilters,
    SearchFilters,
)
from termkeeper.adapters.mcp.server import create_server
from termkeeper.adapters.mcp.tools import TermKeeperMcpTools

__all__ = [
    "CaptureBatchInput",
    "CaptureTermInput",
    "InboxSearchFilters",
    "MeaningFilters",
    "MeaningCreateInput",
    "MeaningEditInput",
    "OccurrenceFilters",
    "OccurrenceSearchFilters",
    "ScopeSearchFilters",
    "SearchFilters",
    "TermKeeperMcpTools",
    "create_server",
]
