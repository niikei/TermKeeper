import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery


def test_merge_meanings_moves_terms_and_occurrences() -> None:
    service = TermKeeperService()
    captured_source = service.add("SRC", source="Teams")
    second_source = service.add("src", source="Slack")
    captured_target = service.add("TGT")
    source = service.resolve(captured_source.occurrence.occurrence_id, "Source Meaning")
    service.assign(second_source.occurrence.occurrence_id, source.meaning_id)
    target = service.resolve(captured_target.occurrence.occurrence_id, "Target Meaning")
    service.add_alias(source.meaning_id, "shared")
    service.add_alias(source.meaning_id, "source-only")
    service.add_alias(target.meaning_id, "shared")
    service.add_tag(source.meaning_id, "source-tag")
    service.add_tag(source.meaning_id, "shared-tag")
    service.add_tag(target.meaning_id, "shared-tag")
    source_reference = service.add_reference(
        source.meaning_id,
        "https://example.com/source",
        "Source guide",
    )
    service.add_reference(
        source.meaning_id,
        "https://example.com/shared",
        "Shared source guide",
    )
    target_reference = service.add_reference(
        target.meaning_id,
        "https://example.com/shared",
    )
    source_related = service.create_meaning("Source related")
    shared_related = service.create_meaning("Shared related")
    service.relate(source.meaning_id, source_related.meaning_id)
    service.relate(source.meaning_id, shared_related.meaning_id)
    service.relate(target.meaning_id, shared_related.meaning_id)
    service.relate(source.meaning_id, target.meaning_id)

    preview = service.merge_meanings(source.meaning_id, target.meaning_id, dry_run=True)

    assert preview.terms_moved == 3
    assert preview.tags_moved == 1
    assert preview.occurrences_moved == 2
    assert preview.references_moved == 1
    assert preview.references_deduplicated == 1
    assert preview.relations_moved == 1
    assert preview.relations_deduplicated == 1
    assert preview.relations_collapsed == 1
    assert preview.applied is False
    assert service.get_meaning(source.meaning_id).full_name == "Source Meaning"
    assert len(service.references(source.meaning_id)) == 2
    assert len(service.related(source.meaning_id)) == 3

    result = service.merge_meanings(source.meaning_id, target.meaning_id)

    assert result.applied is True
    with pytest.raises(NotFoundError):
        service.get_meaning(source.meaning_id)
    merged = service.get_meaning(target.meaning_id)
    assert {"SRC", "Source Meaning", "shared", "source-only"} <= set(merged.terms)
    assert set(merged.tags) == {"source-tag", "shared-tag"}
    assert (
        service.occurrences(
            OccurrenceQuery(meaning_id=source.meaning_id),
        ).items
        == ()
    )
    assert (
        len(
            service.occurrences(
                OccurrenceQuery(meaning_id=target.meaning_id),
            ).items,
        )
        == 3
    )
    references = service.references(target.meaning_id)
    assert {item.url for item in references} == {
        "https://example.com/shared",
        "https://example.com/source",
    }
    assert next(item for item in references if item.url.endswith("/source")).public_id == (
        source_reference.public_id
    )
    shared_reference = next(item for item in references if item.url.endswith("/shared"))
    assert shared_reference.public_id == target_reference.public_id
    assert shared_reference.title == "Shared source guide"
    assert {item.meaning_id for item in service.related(target.meaning_id)} == {
        source_related.meaning_id,
        shared_related.meaning_id,
    }


def test_merge_validation_and_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TermKeeperService()
    source = service.create_meaning("Source", terms=("source-alias",))
    target = service.create_meaning("Target")
    related = service.create_meaning("Related")
    reference = service.add_reference(source.meaning_id, "https://example.com/source")
    service.relate(source.meaning_id, related.meaning_id)

    with pytest.raises(ValidationError):
        service.merge_meanings(source.meaning_id, source.meaning_id)

    def fail_purge(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "termkeeper.application.use_cases.merge.meaning_repository.purge",
        fail_purge,
    )
    with pytest.raises(RuntimeError):
        service.merge_meanings(source.meaning_id, target.meaning_id)

    assert "source-alias" in service.get_meaning(source.meaning_id).terms
    assert "source-alias" not in service.get_meaning(target.meaning_id).terms
    assert service.references(source.meaning_id)[0].public_id == reference.public_id
    assert service.references(target.meaning_id) == []
    assert service.related(source.meaning_id)[0].meaning_id == related.meaning_id
    assert service.related(target.meaning_id) == []
