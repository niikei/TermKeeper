from uuid import UUID

import pytest

from termkeeper.adapters.external import ExternalMapper
from termkeeper.application import TermKeeperService


def test_external_mapper_batches_meaning_public_id_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = TermKeeperService()
    first = service.create_meaning("First")
    second = service.create_meaning("Second")
    service.add("ONE", meaning_id=first.meaning_id)
    service.add("TWO", meaning_id=second.meaning_id)
    service.add_reference(first.meaning_id, "https://example.com/one")
    service.add_reference(first.meaning_id, "https://example.com/two")
    mapper = ExternalMapper(service)
    calls: list[set[int]] = []
    lookup = service.meaning_public_ids

    def track_lookup(meaning_ids: set[int]) -> dict[int, UUID]:
        calls.append(meaning_ids)
        return lookup(meaning_ids)

    monkeypatch.setattr(service, "meaning_public_ids", track_lookup)

    occurrences = mapper.occurrence_page(service.occurrences())
    references = mapper.references(service.references(first.meaning_id))

    assert {item.meaning_id for item in occurrences.items} == {
        first.public_id,
        second.public_id,
    }
    assert {item.meaning_id for item in references} == {first.public_id}
    assert calls == [
        {first.meaning_id, second.meaning_id},
        {first.meaning_id},
    ]
