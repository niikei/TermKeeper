"""Tests for terminal-aware CLI styling."""

import pytest

from termkeeper.adapters.cli import style


def test_styled_adds_ansi_codes_when_color_is_enabled(
) -> None:
    style.configure_color("always")

    assert style.styled("Scope", style.BOLD, style.MAGENTA) == (
        "\033[1;35mScope\033[0m"
    )
    style.configure_color("auto")


def test_styled_is_plain_when_color_is_disabled(
) -> None:
    style.configure_color("never")

    assert style.styled("Scope", style.MAGENTA) == "Scope"
    assert style.styled("Scope") == "Scope"
    style.configure_color("auto")


def test_color_respects_terminal_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    style.configure_color("auto")
    monkeypatch.setattr(style.sys.stdout, "isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    assert style.color_enabled()

    monkeypatch.setenv("NO_COLOR", "")
    assert style.color_enabled()

    monkeypatch.setenv("NO_COLOR", "1")
    assert not style.color_enabled()

    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("TERM", "dumb")
    assert not style.color_enabled()

    monkeypatch.setenv("FORCE_COLOR", "1")
    assert style.color_enabled()


def test_explicit_color_mode_overrides_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    style.configure_color("always")
    assert style.color_enabled()

    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")
    style.configure_color("never")
    assert not style.color_enabled()
    style.configure_color("auto")


@pytest.mark.parametrize(
    ("status", "ansi_code"),
    [
        ("Resolved", "\033[32m"),
        ("Pending", "\033[33m"),
        ("Discarded", "\033[1;31m"),
    ],
)
def test_status_colors_have_consistent_semantics(
    status: str,
    ansi_code: str,
) -> None:
    style.configure_color("always")
    assert style.status_label(status).startswith(ansi_code)
    style.configure_color("auto")
