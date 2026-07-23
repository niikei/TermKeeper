import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError


def test_related_meanings_are_symmetric_idempotent_and_removable() -> None:
    service = TermKeeperService()
    erp = service.create_meaning("Enterprise Resource Planning")
    mrp = service.create_meaning("Material Requirements Planning")
    scm = service.create_meaning("Supply Chain Management")

    related = service.relate(erp.meaning_id, mrp.meaning_id)
    service.relate(mrp.meaning_id, erp.meaning_id)
    service.relate(erp.meaning_id, scm.meaning_id)

    assert [item.meaning_id for item in related] == [mrp.meaning_id]
    assert [item.meaning_id for item in service.related(erp.meaning_id)] == [
        mrp.meaning_id,
        scm.meaning_id,
    ]
    assert [item.meaning_id for item in service.related(mrp.meaning_id)] == [
        erp.meaning_id,
    ]
    with pytest.raises(ValidationError):
        service.relate(erp.meaning_id, erp.meaning_id)
    with pytest.raises(NotFoundError):
        service.relate(erp.meaning_id, 999)

    remaining = service.unrelate(erp.meaning_id, mrp.meaning_id)
    assert [item.meaning_id for item in remaining] == [scm.meaning_id]
    with pytest.raises(NotFoundError):
        service.unrelate(erp.meaning_id, mrp.meaning_id)


def test_related_meanings_hide_soft_deleted_targets() -> None:
    service = TermKeeperService()
    source = service.create_meaning("Source")
    target = service.create_meaning("Target")
    service.relate(source.meaning_id, target.meaning_id)

    service.delete_meaning(target.meaning_id)
    assert service.related(source.meaning_id) == []

    service.restore_meaning(target.meaning_id)
    assert service.related(source.meaning_id)[0].meaning_id == target.meaning_id
