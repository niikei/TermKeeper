"""Shared query operators for filtering and ordering resources."""

from enum import StrEnum


class LogicalOperator(StrEnum):
    ALL = "all"
    ANY = "any"


class MeaningSort(StrEnum):
    NAME = "name"
    CREATED = "created"
    UPDATED = "updated"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"
