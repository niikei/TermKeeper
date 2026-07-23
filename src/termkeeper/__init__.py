"""TermKeeper public package API."""

from importlib.metadata import version

from termkeeper.application import TermKeeperService

__all__ = ["TermKeeperService", "__version__"]
__version__ = version("termkeeper")
