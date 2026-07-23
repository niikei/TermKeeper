from termkeeper.infrastructure import meaning_repository
from termkeeper.infrastructure.connection import get_session


def test_add_term_ignores_empty_keyword() -> None:
    with get_session() as session:
        assert meaning_repository.add_term(session, 1, "  ", None) is False
