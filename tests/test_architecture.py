"""Executable dependency rules for the inbound adapters."""

import ast
from pathlib import Path

from termkeeper.application.use_cases.capture import CaptureUseCases
from termkeeper.application.use_cases.meaning import MeaningUseCases
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
                "termkeeper.infrastructure"
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
    assert "search_meanings" not in MeaningUseCases.__dict__
    assert "search_occurrences" not in OccurrenceUseCases.__dict__
    assert "search_inbox" not in OccurrenceUseCases.__dict__
    assert "search_scopes" not in ScopeUseCases.__dict__


def test_capture_methods_have_one_application_owner() -> None:
    assert {"add", "capture_many"} <= CaptureUseCases.__dict__.keys()
    assert "capture_many" not in OccurrenceUseCases.__dict__


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
