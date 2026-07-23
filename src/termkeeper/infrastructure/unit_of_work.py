"""A small transaction boundary shared by application use cases."""

from types import TracebackType

from sqlmodel import Session

from termkeeper.infrastructure.connection import get_session


class UnitOfWork:
    session: Session

    def __enter__(self) -> "UnitOfWork":
        self.session = get_session()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()
