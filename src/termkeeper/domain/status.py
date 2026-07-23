"""Domain state values."""

from enum import StrEnum


class OccurrenceStatus(StrEnum):
    PENDING = "Pending"
    RESOLVED = "Resolved"
    DISCARDED = "Discarded"
