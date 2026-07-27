from sqlalchemy import Engine, event

from termkeeper.application import TermKeeperService
from termkeeper.domain import CaptureInput, MeaningListQuery, SearchMode, SearchQuery
from termkeeper.infrastructure.connection import get_engine


def test_meaning_pages_and_searches_use_bounded_query_counts() -> None:
    service = TermKeeperService()
    for index in range(50):
        meaning = service.create_meaning(
            f"Planning Concept {index:02}",
            "Enterprise planning",
            terms=(f"PC{index:02}",),
        )
        service.add_tag(meaning.meaning_id, "Core")

    counter = _QueryCounter(get_engine())
    with counter:
        page = service.meaning_page(MeaningListQuery(limit=50))
    assert len(page.items) == 50
    assert counter.count == 4

    with counter:
        smart = service.search_meanings(SearchQuery("Planning", limit=50))
    assert len(smart.hits) == 50
    assert counter.count == 4

    with counter:
        glob = service.search_meanings(
            SearchQuery("Planning*", mode=SearchMode.GLOB, limit=50),
        )
    assert len(glob.hits) == 50
    assert counter.count == 4


def test_batch_capture_candidate_queries_have_constant_overhead() -> None:
    service = TermKeeperService()
    inputs: list[CaptureInput] = []
    for index in range(20):
        keyword = f"PC{index:02}"
        service.create_meaning(
            f"Planning Concept {index:02}",
            terms=(keyword,),
        )
        inputs.append(CaptureInput(keyword))

    counter = _QueryCounter(get_engine())
    with counter:
        result = service.capture_many(tuple(inputs))

    assert len(result.items) == len(inputs)
    assert all(len(item.candidates) == 1 for item in result.items)
    assert counter.count <= len(inputs) + 5


class _QueryCounter:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self.count = 0

    def __enter__(self) -> None:
        self.count = 0
        event.listen(self._engine, "before_cursor_execute", self._increment)

    def __exit__(self, *_args: object) -> None:
        event.remove(self._engine, "before_cursor_execute", self._increment)

    def _increment(self, *_args: object) -> None:
        self.count += 1
