"""Feature-oriented MCP tool collection."""

from termkeeper.adapters.mcp.tools.capture import CaptureTools
from termkeeper.adapters.mcp.tools.meaning import MeaningTools
from termkeeper.adapters.mcp.tools.metadata import MetadataTools
from termkeeper.adapters.mcp.tools.occurrence import OccurrenceTools
from termkeeper.adapters.mcp.tools.reference import ReferenceTools
from termkeeper.adapters.mcp.tools.scope import ScopeTools
from termkeeper.adapters.mcp.tools.search import SearchTools


class TermKeeperMcpTools(
    CaptureTools,
    SearchTools,
    MeaningTools,
    OccurrenceTools,
    MetadataTools,
    ReferenceTools,
    ScopeTools,
):
    """Complete typed MCP tool surface."""


__all__ = ["TermKeeperMcpTools"]
