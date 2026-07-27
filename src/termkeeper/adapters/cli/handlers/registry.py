"""Command-to-handler registry."""

from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from termkeeper.adapters.cli.types import CommandHandler

_HANDLERS = {
    "dashboard": ("system", "handle_dashboard"),
    "init": ("transfer", "handle_init"),
    "add": ("capture", "handle_add"),
    "add-many": ("capture_batch", "handle_add_many"),
    "inbox": ("capture", "handle_inbox"),
    "inbox-search": ("capture", "handle_inbox_search"),
    "history": ("capture", "handle_history"),
    "occurrences": ("capture", "handle_occurrences"),
    "occurrence-search": ("capture", "handle_occurrence_search"),
    "occurrence-edit": ("capture", "handle_occurrence_edit"),
    "stats": ("capture", "handle_stats"),
    "resolve": ("capture", "handle_resolve"),
    "unresolve": ("capture", "handle_unresolve"),
    "search": ("meaning", "handle_search"),
    "discard": ("capture", "handle_discard"),
    "reopen": ("capture", "handle_reopen"),
    "show": ("meaning", "handle_show"),
    "term-list": ("meaning", "handle_term_list"),
    "alias": ("meaning", "handle_alias"),
    "unalias": ("meaning", "handle_unalias"),
    "delete": ("meaning", "handle_delete"),
    "trash": ("meaning", "handle_trash"),
    "restore": ("meaning", "handle_restore"),
    "purge": ("meaning", "handle_purge"),
    "merge": ("meaning", "handle_merge"),
    "tag": ("metadata", "handle_tag"),
    "untag": ("metadata", "handle_untag"),
    "tags": ("metadata", "handle_tags"),
    "favorite": ("metadata", "handle_favorite"),
    "unfavorite": ("metadata", "handle_unfavorite"),
    "relate": ("metadata", "handle_relate"),
    "unrelate": ("metadata", "handle_unrelate"),
    "related": ("metadata", "handle_related"),
    "reference-add": ("metadata", "handle_reference_add"),
    "reference-edit": ("metadata", "handle_reference_edit"),
    "reference-remove": ("metadata", "handle_reference_remove"),
    "references": ("metadata", "handle_references"),
    "scope-add": ("scope", "handle_scope_add"),
    "scopes": ("scope", "handle_scopes"),
    "scope-search": ("scope", "handle_scope_search"),
    "scope-edit": ("scope", "handle_scope_edit"),
    "scope-delete": ("scope", "handle_scope_delete"),
    "edit": ("meaning", "handle_edit"),
    "meanings": ("meaning", "handle_meanings"),
    "config": ("config", "handle_config"),
    "doctor": ("system", "handle_doctor"),
    "export": ("transfer", "handle_export"),
    "import": ("transfer", "handle_import"),
}


def get_handler(command: str) -> "CommandHandler":
    module_name, function_name = _HANDLERS[command]
    module = import_module(f"termkeeper.adapters.cli.handlers.{module_name}")
    return cast("CommandHandler", getattr(module, function_name))
