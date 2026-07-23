"""Operational diagnostics returned by the application boundary."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SystemDiagnostics:
    database_backend: str
    database_target: str
    schema_revision: str
    expected_schema_revision: str
    schema_issues: tuple[str, ...]
    configured_keys: frozenset[str]

    @property
    def schema_ok(self) -> bool:
        return self.schema_revision == self.expected_schema_revision and not self.schema_issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
