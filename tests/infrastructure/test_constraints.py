import pytest
from sqlalchemy.exc import IntegrityError

from termkeeper.infrastructure.connection import get_session
from termkeeper.infrastructure.tables import Inbox


def test_database_rejects_duplicate_open_inbox() -> None:
    with get_session() as session:
        session.add(Inbox(keyword="CRM", keyword_norm="crm"))
        session.add(Inbox(keyword="crm", keyword_norm="crm"))

        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
