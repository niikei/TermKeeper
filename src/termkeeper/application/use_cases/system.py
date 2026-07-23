"""Operational use cases for diagnostics and database maintenance."""

from pathlib import Path

from termkeeper.application.errors import ValidationError
from termkeeper.domain import SystemDiagnostics
from termkeeper.infrastructure.connection import get_engine
from termkeeper.infrastructure.repositories import settings_repository
from termkeeper.infrastructure.schema import (
    reset_sqlite_database,
    schema_issues,
    schema_revisions,
)
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class SystemUseCases:
    def diagnostics(self) -> SystemDiagnostics:
        engine = get_engine()
        current_revision, expected_revision = schema_revisions()
        issues = schema_issues()
        configured_keys: frozenset[str]
        if any("userprofile" in issue for issue in issues):
            configured_keys = frozenset()
        else:
            with UnitOfWork() as uow:
                profile = settings_repository.get_profile(uow.session)
                configured_keys = frozenset(settings_repository.as_config(profile))
        return SystemDiagnostics(
            database_backend=engine.dialect.name,
            database_target=engine.url.render_as_string(hide_password=True),
            schema_revision=current_revision or "missing",
            expected_schema_revision=expected_revision,
            schema_issues=issues,
            configured_keys=configured_keys,
        )

    def reset_database(self) -> Path | None:
        try:
            return reset_sqlite_database()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
