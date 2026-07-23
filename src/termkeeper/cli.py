"""Compatibility CLI entry point; implementation lives in presentation."""

from termkeeper.presentation.main import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
