from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.repositories import meaning_repository


def test_add_term_ignores_empty_keyword() -> None:
    with get_session() as session:
        assert meaning_repository.add_term(session, 1, "  ", None) is False
