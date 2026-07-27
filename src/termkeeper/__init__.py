"""TermKeeper public package API."""

from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from termkeeper.application import TermKeeperService

__all__ = ["TermKeeperService", "__version__"]
__version__ = version("termkeeper")


def __getattr__(name: str) -> object:
    """Load the application facade only when callers request it."""
    if name == "TermKeeperService":
        from termkeeper.application import TermKeeperService

        return TermKeeperService
    message = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(message)
