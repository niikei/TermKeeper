import pytest

from termkeeper.application import InitializationError, TermKeeperService


def test_diagnostics_hide_dependency_errors_and_readiness_degrades(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_revision_check() -> tuple[str | None, str]:
        message = "database unavailable"
        raise RuntimeError(message)

    monkeypatch.setattr(
        "termkeeper.application.use_cases.system.schema_revisions",
        fail_revision_check,
    )
    service = TermKeeperService()

    with pytest.raises(InitializationError, match="--debug doctor"):
        service.diagnostics()
    assert service.readiness().status == "unavailable"
