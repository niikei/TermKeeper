from uuid import uuid4

import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import ReferenceUpdate


def test_reference_links_support_crud_and_validation() -> None:
    service = TermKeeperService()
    service.set_config("user.name", "Researcher")
    meaning = service.create_meaning("Enterprise Resource Planning")

    with pytest.raises(ValidationError):
        service.add_reference(meaning.meaning_id, "example.com")
    created = service.add_reference(
        meaning.meaning_id,
        " https://example.com/erp ",
        " ERP guide ",
    )
    duplicate = service.add_reference(meaning.meaning_id, created.url, "Ignored")
    second = service.add_reference(meaning.meaning_id, "https://example.com/overview")

    assert duplicate.reference_id == created.reference_id
    assert [item.reference_id for item in service.references(meaning.meaning_id)] == [
        created.reference_id,
        second.reference_id,
    ]
    updated = service.edit_reference(
        created.reference_id,
        ReferenceUpdate(url="https://docs.example.com/erp", title="Official guide"),
    )
    assert updated.url == "https://docs.example.com/erp"
    assert updated.title == "Official guide"
    assert updated.updated_by_id is not None
    cleared = service.edit_reference(
        created.public_id,
        ReferenceUpdate(clear_title=True),
    )
    assert cleared.title is None

    with pytest.raises(ValidationError):
        service.edit_reference(created.reference_id, ReferenceUpdate())
    with pytest.raises(ValidationError):
        service.edit_reference(
            created.reference_id,
            ReferenceUpdate(title="Conflict", clear_title=True),
        )
    with pytest.raises(ValidationError):
        service.edit_reference(
            created.reference_id,
            ReferenceUpdate(url=second.url),
        )
    with pytest.raises(NotFoundError):
        service.edit_reference(999, ReferenceUpdate(title="Missing"))

    removed = service.remove_reference(created.reference_id)
    assert removed.reference_id == created.reference_id
    with pytest.raises(NotFoundError):
        service.remove_reference(created.reference_id)
    with pytest.raises(NotFoundError):
        service.remove_reference(uuid4())
