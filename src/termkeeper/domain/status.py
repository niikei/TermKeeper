"""Domain state values."""

from enum import StrEnum


class InboxStatus(StrEnum):
    NEW = "New"
    CLOSED = "Closed"
    DISCARDED = "Discarded"
