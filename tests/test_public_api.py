"""Public package API compatibility."""

import pytest

import termkeeper
from termkeeper.application import TermKeeperService


def test_lazy_service_export_resolves_to_application_facade() -> None:
    assert termkeeper.TermKeeperService is TermKeeperService


def test_unknown_public_attribute_is_rejected() -> None:
    with pytest.raises(AttributeError, match="has no attribute"):
        termkeeper.__getattr__("unknown")
