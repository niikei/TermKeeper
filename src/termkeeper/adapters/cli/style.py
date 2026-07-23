"""Terminal-aware ANSI styling for human-readable CLI output."""

import os
import sys
from dataclasses import dataclass
from typing import Literal, TextIO

BOLD = "1"
DIM = "2"
UNDERLINE = "4"
RED = "31"
GREEN = "32"
YELLOW = "33"
BLUE = "34"
MAGENTA = "35"
CYAN = "36"

ColorMode = Literal["auto", "always", "never"]


@dataclass
class _StyleConfig:
    color_mode: ColorMode = "auto"


_CONFIG = _StyleConfig()


def configure_color(mode: ColorMode) -> None:
    """Set color behavior for the current CLI invocation."""
    _CONFIG.color_mode = mode


def color_enabled(*, stream: TextIO | None = None) -> bool:
    """Return whether ANSI styling is appropriate for the current output."""
    output = stream or sys.stdout
    if _CONFIG.color_mode == "never":
        return False
    if _CONFIG.color_mode == "always":
        return True
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return output.isatty() and os.environ.get("TERM") != "dumb"


def styled(
    text: str,
    *codes: str,
    stream: TextIO | None = None,
) -> str:
    """Apply ANSI codes when writing to an interactive color terminal."""
    if not codes or not color_enabled(stream=stream):
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def heading(text: str) -> str:
    return styled(text, BOLD)


def identifier(text: str) -> str:
    return styled(text, BOLD, CYAN)


def scope_label(text: str) -> str:
    return styled(text, MAGENTA)


def command(text: str) -> str:
    return styled(text, CYAN)


def success(text: str) -> str:
    return styled(text, GREEN)


def warning(text: str) -> str:
    return styled(text, YELLOW)


def danger(text: str, *, stream: TextIO | None = None) -> str:
    return styled(text, BOLD, RED, stream=stream)


def muted(text: str) -> str:
    return styled(text, DIM)


def status_label(status: str) -> str:
    normalized = status.casefold()
    if normalized == "resolved":
        return success(status)
    if normalized == "pending":
        return warning(status)
    if normalized == "discarded":
        return danger(status)
    return status
