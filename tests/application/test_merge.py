import pytest

from termkeeper.application import NotFoundError, TermKeeperService, ValidationError
from termkeeper.domain import OccurrenceQuery


def test_merge_meanings_moves_terms_occurrences_and_inboxes() -> None:
    service = TermKeeperService()
    captured_source = service.add("SRC", source="Teams")
    service.add("src", source="Slack")
    captured_target = service.add("TGT")
    assert captured_source.inbox is not None
    assert captured_target.inbox is not None
    source = service.resolve(captured_source.inbox.inbox_id, "Source Meaning")
    target = service.resolve(captured_target.inbox.inbox_id, "Target Meaning")
    service.add_alias(source.meaning_id, "shared")
    service.add_alias(source.meaning_id, "source-only")
    service.add_alias(target.meaning_id, "shared")
    service.add_tag(source.meaning_id, "source-tag")
    service.add_tag(source.meaning_id, "shared-tag")
    service.add_tag(target.meaning_id, "shared-tag")

    preview = service.merge_meanings(source.meaning_id, target.meaning_id, dry_run=True)

    assert preview.terms_moved == 3
    assert preview.tags_moved == 1
    assert preview.occurrences_moved == 2
    assert preview.inboxes_moved == 1
    assert preview.applied is False
    assert service.get_meaning(source.meaning_id).full_name == "Source Meaning"

    result = service.merge_meanings(source.meaning_id, target.meaning_id)

    assert result.applied is True
    with pytest.raises(NotFoundError):
        service.get_meaning(source.meaning_id)
    merged = service.get_meaning(target.meaning_id)
    assert {"SRC", "Source Meaning", "shared", "source-only"} <= set(merged.terms)
    assert set(merged.tags) == {"source-tag", "shared-tag"}
    assert service.occurrences(OccurrenceQuery(meaning_id=source.meaning_id)) == []
    assert len(service.occurrences(OccurrenceQuery(meaning_id=target.meaning_id))) == 3
    source_inbox = service.get_inbox(captured_source.inbox.inbox_id)
    assert source_inbox.resolved_meaning_id == target.meaning_id


def test_merge_validation_and_rollback(monkeypatch: pytest.MonkeyPatch) -> None:
    service = TermKeeperService()
    source = service.create_meaning("Source", terms=("source-alias",))
    target = service.create_meaning("Target")

    with pytest.raises(ValidationError):
        service.merge_meanings(source.meaning_id, source.meaning_id)

    def fail_move(*_args: object, **_kwargs: object) -> tuple[int, int]:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(
        "termkeeper.application.use_cases.merge.inbox_repository.move_meaning_references",
        fail_move,
    )
    with pytest.raises(RuntimeError):
        service.merge_meanings(source.meaning_id, target.meaning_id)

    assert "source-alias" in service.get_meaning(source.meaning_id).terms
    assert "source-alias" not in service.get_meaning(target.meaning_id).terms
