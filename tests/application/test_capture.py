from uuid import uuid4

import pytest
from sqlmodel import func, select

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceStatus
from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Meaning as MeaningRecord


def test_capture_always_creates_independent_pending_occurrences() -> None:
    service = TermKeeperService()

    first = service.add("\uff2d\uff24\uff2d", memo="meeting")
    second = service.add("mdm", source="chat")

    assert first.occurrence.occurrence_id != second.occurrence.occurrence_id
    assert first.occurrence.status == OccurrenceStatus.PENDING
    assert second.occurrence.status == OccurrenceStatus.PENDING
    assert len(service.inbox().items) == 2


def test_capture_suggests_all_matching_meanings_without_assigning() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    service.create_scope("Radio")
    sap = service.create_meaning(
        "Enterprise Resource Planning",
        terms=("ERP",),
        scope="SAP",
    )
    energy = service.create_meaning(
        "Effective Radiated Power",
        terms=("ERP",),
        scope="Radio",
    )

    captured = service.add("erp", memo="ambiguous")

    assert captured.occurrence.status == OccurrenceStatus.PENDING
    assert captured.occurrence.meaning_id is None
    assert {item.meaning_id for item in captured.candidates} == {
        sap.meaning_id,
        energy.meaning_id,
    }


def test_capture_can_explicitly_assign_a_known_meaning() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    meaning = service.create_meaning("Enterprise Resource Planning", scope="SAP")

    captured = service.add("ERP", meaning_id=meaning.meaning_id)

    assert captured.occurrence.status == OccurrenceStatus.RESOLVED
    assert captured.occurrence.meaning_id == meaning.meaning_id
    assert captured.candidates == ()


def test_resolve_creates_scoped_meaning_and_classifies_only_one_occurrence() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    first = service.add("ERP")
    second = service.add("ERP")

    meaning = service.resolve(
        first.occurrence.occurrence_id,
        "Enterprise Resource Planning",
        "SAP platform",
        "SAP",
    )

    assert meaning.scope == "SAP"
    assert set(meaning.terms) == {"ERP", "Enterprise Resource Planning"}
    assert service.get_occurrence(first.occurrence.occurrence_id).status == "Resolved"
    assert service.get_occurrence(second.occurrence.occurrence_id).status == "Pending"
    assert len(service.inbox().items) == 1


def test_assignment_can_be_corrected_and_discard_can_be_reopened() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    service.create_scope("Radio")
    sap = service.create_meaning("Enterprise Resource Planning", scope="SAP")
    radio = service.create_meaning("Effective Radiated Power", scope="Radio")
    occurrence_id = service.add("ERP").occurrence.occurrence_id

    assigned = service.assign(occurrence_id, sap.meaning_id)
    reassigned = service.assign(occurrence_id, radio.meaning_id)
    pending = service.unresolve(occurrence_id)
    discarded = service.discard(occurrence_id)
    reopened = service.reopen(occurrence_id)

    assert assigned.meaning_id == sap.meaning_id
    assert reassigned.meaning_id == radio.meaning_id
    assert pending.status == OccurrenceStatus.PENDING
    assert discarded.status == OccurrenceStatus.DISCARDED
    assert reopened.status == OccurrenceStatus.PENDING


def test_classification_state_transitions_are_validated() -> None:
    service = TermKeeperService()
    service.create_scope("SAP")
    occurrence_id = service.add("ERP").occurrence.occurrence_id
    meaning = service.create_meaning("Enterprise Resource Planning", scope="SAP")

    with pytest.raises(ValidationError):
        service.unresolve(occurrence_id)
    service.discard(occurrence_id)
    with pytest.raises(ValidationError):
        service.assign(occurrence_id, meaning.meaning_id)
    with pytest.raises(ValidationError):
        service.resolve(occurrence_id, "Another")
    service.reopen(occurrence_id)
    service.assign(occurrence_id, meaning.meaning_id)
    with pytest.raises(ValidationError):
        service.discard(occurrence_id)


def test_occurrence_public_id_and_validation_errors_are_explicit() -> None:
    service = TermKeeperService()
    captured = service.add("TX")

    assert (
        service.get_occurrence_by_public_id(captured.occurrence.public_id).occurrence_id
        == captured.occurrence.occurrence_id
    )
    with pytest.raises(NotFoundError):
        service.get_occurrence_by_public_id(uuid4())
    with pytest.raises(ValidationError):
        service.add(" ")
    with pytest.raises(NotFoundError):
        service.add("ERP", meaning_id=999)


def test_capture_normalizes_and_validates_optional_context() -> None:
    service = TermKeeperService()

    captured = service.add(" ERP ", memo=" planning ", source=" Teams ")

    assert captured.occurrence.keyword == "ERP"
    assert captured.occurrence.memo == "planning"
    assert captured.occurrence.source == "Teams"
    with pytest.raises(ValidationError, match="Memo must not be empty"):
        service.add("ERP", memo=" ")
    with pytest.raises(ValidationError, match="Source must not be empty"):
        service.add("ERP", source=" ")


def test_resolve_rolls_back_all_changes_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TermKeeperService()
    captured = service.add("TX")

    def fail_add_term(*_args: object, **_kwargs: object) -> bool:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "termkeeper.application.use_cases.capture.meaning_repository.add_term",
        fail_add_term,
    )
    with pytest.raises(RuntimeError):
        service.resolve(captured.occurrence.occurrence_id, "Transaction")

    assert service.get_occurrence(captured.occurrence.occurrence_id).status == "Pending"
    with get_session() as session:
        meaning_count = session.exec(select(func.count()).select_from(MeaningRecord)).one()
    assert meaning_count == 0
