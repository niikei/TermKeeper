"""Executable dependency rules for the inbound adapters."""

import ast
import inspect
from importlib import import_module
from pathlib import Path

from termkeeper.application.service import _USE_CASES
from termkeeper.application.use_cases.capture import CaptureUseCases
from termkeeper.application.use_cases.classification import ClassificationUseCases
from termkeeper.application.use_cases.meaning_command import MeaningCommandUseCases
from termkeeper.application.use_cases.meaning_lifecycle import MeaningLifecycleUseCases
from termkeeper.application.use_cases.meaning_query import MeaningQueryUseCases
from termkeeper.application.use_cases.occurrence import OccurrenceUseCases
from termkeeper.application.use_cases.scope import ScopeUseCases
from termkeeper.application.use_cases.search import SearchUseCases

ADAPTER_ROOT = Path("src/termkeeper/adapters")


def test_inbound_adapters_do_not_import_infrastructure() -> None:
    violations: list[str] = []
    for path in ADAPTER_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "termkeeper.infrastructure",
            ):
                violations.append(f"{path}:{node.lineno}")
            if isinstance(node, ast.Import):
                violations.extend(
                    f"{path}:{node.lineno}"
                    for alias in node.names
                    if alias.name.startswith("termkeeper.infrastructure")
                )
    assert violations == []


def test_resource_search_methods_have_one_application_owner() -> None:
    assert {
        "search_meanings",
        "search_occurrences",
        "search_inbox",
        "search_scopes",
    } <= SearchUseCases.__dict__.keys()
    assert "search_meanings" not in MeaningQueryUseCases.__dict__
    assert "search_occurrences" not in OccurrenceUseCases.__dict__
    assert "search_inbox" not in OccurrenceUseCases.__dict__
    assert "search_scopes" not in ScopeUseCases.__dict__


def test_capture_methods_have_one_application_owner() -> None:
    assert {"add", "capture_many"} <= CaptureUseCases.__dict__.keys()
    assert "capture_many" not in OccurrenceUseCases.__dict__
    assert "resolve" not in CaptureUseCases.__dict__
    assert {"resolve", "assign", "unresolve", "discard", "reopen"} <= (
        ClassificationUseCases.__dict__.keys()
    )


def test_meaning_responsibilities_have_distinct_application_owners() -> None:
    assert {"meaning_page", "get_meaning"} <= MeaningQueryUseCases.__dict__.keys()
    assert {"create_meaning", "edit", "add_alias"} <= MeaningCommandUseCases.__dict__.keys()
    assert {"delete_meaning", "restore_meaning", "purge_meaning"} <= (
        MeaningLifecycleUseCases.__dict__.keys()
    )
    owners = (
        MeaningQueryUseCases,
        MeaningCommandUseCases,
        MeaningLifecycleUseCases,
    )
    for method in ("meaning_page", "create_meaning", "delete_meaning"):
        assert sum(method in owner.__dict__ for owner in owners) == 1


def test_lazy_service_registry_covers_every_use_case_method_once() -> None:
    registered: list[str] = []
    for module_name, class_name, method_names in _USE_CASES:
        module = import_module(f"termkeeper.application.use_cases.{module_name}")
        use_case = getattr(module, class_name)
        actual = {name for name, value in vars(use_case).items() if inspect.isfunction(value)}
        assert set(method_names) == actual, f"{class_name} registry is stale"
        registered.extend(method_names)

    assert len(registered) == len(set(registered))


def test_batch_capture_adapters_delegate_once_to_shared_use_case() -> None:
    functions = (
        (
            Path("src/termkeeper/adapters/cli/handlers/capture_batch.py"),
            "handle_add_many",
        ),
        (
            Path("src/termkeeper/adapters/http/routes/capture.py"),
            "capture_batch",
        ),
        (
            Path("src/termkeeper/adapters/mcp/tools/capture.py"),
            "capture_terms",
        ),
    )
    for path, function_name in functions:
        function = _function(path, function_name)
        calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "capture_many"
        ]
        assert len(calls) == 1, f"{path}:{function_name} must call capture_many exactly once"


def _function(path: Path, name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{path} has no function named {name}")
