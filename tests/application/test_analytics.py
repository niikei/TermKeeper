import pytest

from termkeeper.application import TermKeeperService, ValidationError


def test_stats_summarizes_and_ranks_occurrences() -> None:
    service = TermKeeperService()
    captured = service.add("ERP", source="Teams")
    service.add("erp", source="teams")
    service.add("CRM", source="Slack")
    assert captured.inbox is not None
    service.resolve(captured.inbox.inbox_id, "Enterprise Resource Planning")

    stats = service.stats(limit=1)

    assert stats.total_occurrences == 3
    assert stats.open_inbox_items == 1
    assert stats.active_meanings == 1
    assert [(item.value, item.count) for item in stats.top_terms] == [("ERP", 2)]
    assert [(item.value, item.count) for item in stats.top_sources] == [("Teams", 2)]
    assert stats.top_terms[0].last_seen_at is not None
    with pytest.raises(ValidationError):
        service.stats(0)
    with pytest.raises(ValidationError):
        service.stats(101)
