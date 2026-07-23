"""Occurrence analytics use cases."""

from termkeeper.application.errors import ValidationError
from termkeeper.domain import Frequency, StatsSummary
from termkeeper.infrastructure.repositories import analytics_repository
from termkeeper.infrastructure.unit_of_work import UnitOfWork


class AnalyticsUseCases:
    def stats(self, limit: int = 10) -> StatsSummary:
        if not 1 <= limit <= 100:
            message = "Stats limit must be between 1 and 100."
            raise ValidationError(message)
        with UnitOfWork() as uow:
            return StatsSummary(
                total_occurrences=analytics_repository.count_occurrences(uow.session),
                pending_occurrences=analytics_repository.count_pending_occurrences(uow.session),
                active_meanings=analytics_repository.count_active_meanings(uow.session),
                top_terms=tuple(
                    Frequency(value, count, last_seen)
                    for value, count, last_seen in analytics_repository.top_terms(
                        uow.session,
                        limit,
                    )
                ),
                top_sources=tuple(
                    Frequency(value, count, last_seen)
                    for value, count, last_seen in analytics_repository.top_sources(
                        uow.session,
                        limit,
                    )
                ),
            )
