from uuid import uuid4

import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError


def test_scope_lifecycle_and_stable_identity() -> None:
    service = TermKeeperService()

    scope = service.create_scope(" SAP ", "Enterprise platform")
    updated = service.edit_scope(scope.scope_id, "SAP S/4HANA", "Current platform")

    assert updated.public_id == scope.public_id
    assert updated.name == "SAP S/4HANA"
    assert updated.description == "Current platform"
    assert service.get_scope_by_public_id(scope.public_id) == updated
    assert [item.name for item in service.scopes()] == ["General", "SAP S/4HANA"]

    service.delete_scope(scope.scope_id)
    with pytest.raises(NotFoundError):
        service.get_scope(scope.scope_id)


def test_scope_names_are_normalized_and_validated() -> None:
    service = TermKeeperService()
    scope = service.create_scope("SAP")

    with pytest.raises(ValidationError, match="already exists"):
        service.create_scope(" sap ")
    with pytest.raises(ValidationError, match="must not be empty"):
        service.create_scope(" ")
    with pytest.raises(NotFoundError):
        service.get_scope_by_public_id(uuid4())

    service.create_scope("Other")
    with pytest.raises(ValidationError, match="already exists"):
        service.edit_scope(scope.scope_id, "other", None)


def test_default_and_referenced_scopes_cannot_be_deleted() -> None:
    service = TermKeeperService()

    with pytest.raises(ValidationError, match="General"):
        service.delete_scope(1)

    scope = service.create_scope("SAP")
    service.create_meaning("Order", scope="SAP")
    with pytest.raises(ValidationError, match="used by 1 meaning"):
        service.delete_scope(scope.scope_id)
