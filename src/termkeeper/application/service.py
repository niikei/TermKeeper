"""Lazy public application facade for CLI, HTTP, and MCP adapters."""

from importlib import import_module
from types import MethodType
from typing import TYPE_CHECKING

from termkeeper.application.errors import InitializationError

_USE_CASES = (
    ("analytics", "AnalyticsUseCases", ("stats",)),
    ("capture", "CaptureUseCases", ("add", "capture_many")),
    (
        "classification",
        "ClassificationUseCases",
        (
            "get_occurrence",
            "resolution_options",
            "get_occurrence_by_public_id",
            "resolve",
            "assign",
            "unresolve",
            "discard",
            "reopen",
        ),
    ),
    ("config", "ConfigUseCases", ("set_config", "get_config", "list_config", "unset_config")),
    ("importing", "ImportUseCases", ("import_meanings",)),
    (
        "meaning_command",
        "MeaningCommandUseCases",
        (
            "create_meaning",
            "favorite_meaning",
            "unfavorite_meaning",
            "add_alias",
            "remove_alias",
            "edit",
            "_set_favorite",
        ),
    ),
    (
        "meaning_lifecycle",
        "MeaningLifecycleUseCases",
        ("delete_meaning", "trash", "trash_page", "restore_meaning", "purge_meaning"),
    ),
    (
        "meaning_query",
        "MeaningQueryUseCases",
        (
            "meaning_page",
            "get_meaning",
            "get_meaning_by_public_id",
            "meaning_public_ids",
            "meanings",
        ),
    ),
    ("merge", "MergeUseCases", ("merge_meanings",)),
    (
        "occurrence",
        "OccurrenceUseCases",
        ("occurrences", "inbox", "history", "edit_occurrence", "edit_occurrence_by_public_id"),
    ),
    (
        "reference",
        "ReferenceUseCases",
        ("reference_page", "references", "add_reference", "edit_reference", "remove_reference"),
    ),
    ("relation", "RelationUseCases", ("related_page", "related", "relate", "unrelate")),
    (
        "scope",
        "ScopeUseCases",
        (
            "scope_page",
            "create_scope",
            "get_scope",
            "scopes",
            "get_scope_by_public_id",
            "edit_scope",
            "delete_scope",
        ),
    ),
    (
        "search",
        "SearchUseCases",
        ("search_meanings", "search_occurrences", "search_inbox", "search_scopes"),
    ),
    ("system", "SystemUseCases", ("readiness", "diagnostics", "reset_database")),
    ("tag", "TagUseCases", ("tag_page", "add_tag", "remove_tag", "tags")),
)
_METHOD_TARGETS = {
    method_name: (module_name, class_name)
    for module_name, class_name, method_names in _USE_CASES
    for method_name in method_names
}


class _ServiceBase:
    def initialize(self) -> None:
        from termkeeper.config import database_target

        try:
            init_db()
        except Exception as exc:
            from termkeeper.infrastructure.schema import SchemaMismatchError

            if isinstance(exc, SchemaMismatchError):
                raise InitializationError(str(exc)) from exc
            target = database_target()
            message = (
                f"Could not initialize the TermKeeper database at '{target}'. "
                "Run 'tk --debug init' for technical details."
            )
            raise InitializationError(message) from exc


def init_db() -> None:
    """Load migration support only when database initialization is requested."""
    from termkeeper.infrastructure.schema import init_db as initialize_schema

    initialize_schema()


if TYPE_CHECKING:
    from termkeeper.application.use_cases import (
        AnalyticsUseCases,
        CaptureUseCases,
        ClassificationUseCases,
        ConfigUseCases,
        ImportUseCases,
        MeaningCommandUseCases,
        MeaningLifecycleUseCases,
        MeaningQueryUseCases,
        MergeUseCases,
        OccurrenceUseCases,
        ReferenceUseCases,
        RelationUseCases,
        ScopeUseCases,
        SearchUseCases,
        SystemUseCases,
        TagUseCases,
    )

    class TermKeeperService(
        _ServiceBase,
        AnalyticsUseCases,
        CaptureUseCases,
        ClassificationUseCases,
        ImportUseCases,
        MeaningCommandUseCases,
        MeaningLifecycleUseCases,
        MeaningQueryUseCases,
        MergeUseCases,
        OccurrenceUseCases,
        ReferenceUseCases,
        RelationUseCases,
        ScopeUseCases,
        SearchUseCases,
        SystemUseCases,
        TagUseCases,
        ConfigUseCases,
    ):
        """Stable, statically typed application facade."""

else:

    class TermKeeperService(_ServiceBase):
        """Stable application facade that loads features on first use."""

        def __getattr__(self, name: str) -> object:
            target = _METHOD_TARGETS.get(name)
            if target is None:
                message = f"{type(self).__name__!s} has no attribute {name!r}"
                raise AttributeError(message)
            module_name, class_name = target
            module = import_module(f"termkeeper.application.use_cases.{module_name}")
            method = getattr(getattr(module, class_name), name)
            bound_method = MethodType(method, self)
            setattr(self, name, bound_method)
            return bound_method
