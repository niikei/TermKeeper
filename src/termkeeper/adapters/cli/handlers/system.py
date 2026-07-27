"""Dashboard, diagnostics, and shell integration handlers."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from termkeeper import __version__
from termkeeper.adapters.cli.style import (
    command,
    danger,
    heading,
    muted,
    success,
    warning,
)

if TYPE_CHECKING:
    from termkeeper.application import TermKeeperService

_ROOT_COMMANDS = (
    "add inbox list resolve search show history stats occurrence meaning tag reference "
    "scope data config doctor completion init --help --version --json --debug --color"
)
_GROUP_COMMANDS = {
    "inbox": "search",
    "occurrence": "search list edit unresolve discard reopen",
    "meaning": (
        "search list edit alias-add alias-remove favorite unfavorite relate unrelate related "
        "merge delete trash restore purge"
    ),
    "tag": "add remove list",
    "reference": "add edit remove list",
    "scope": "search add list edit delete",
    "data": "export import",
}


def handle_dashboard(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> dict[str, int]:
    stats = service.stats(limit=1)
    result = {
        "pending_occurrences": stats.pending_occurrences,
        "meanings": stats.active_meanings,
        "scopes": len(service.scopes()),
    }
    if not args.json:
        print(heading(f"TermKeeper {__version__}"))
        print()
        pending = (
            warning(str(stats.pending_occurrences)) if stats.pending_occurrences else success("0")
        )
        print(f"{pending} pending occurrence(s)")
        print(f"{stats.active_meanings} meaning(s) across {result['scopes']} scope(s)")
        print()
        print(heading("Next:"))
        print(f"  {command('tk inbox')}")
        print(f"  {command('tk list')}")
        print(f"  {command('tk add TERM')}")
        print()
        print(muted("Run 'tk --help' for all commands."))
    return result


def handle_doctor(
    args: argparse.Namespace,
    service: TermKeeperService,
) -> dict[str, str]:
    diagnostics = service.diagnostics()
    result = {
        "status": "ok" if diagnostics.schema_ok else "error",
        "version": __version__,
        "database_backend": diagnostics.database_backend,
        "database_target": diagnostics.database_target,
        "schema_revision": diagnostics.schema_revision,
        "expected_schema_revision": diagnostics.expected_schema_revision,
        "schema_issues": (
            "; ".join(diagnostics.schema_issues) if diagnostics.schema_issues else "none"
        ),
        "user.name": ("configured" if "user.name" in diagnostics.configured_keys else "missing"),
        "user.email": ("configured" if "user.email" in diagnostics.configured_keys else "missing"),
    }
    if not args.json:
        print(heading(f"TermKeeper {__version__}"))
        print(
            f"{success('[ok]')} Database: {result['database_backend']} "
            f"({result['database_target']})",
        )
        styled_marker = success("[ok]") if diagnostics.schema_ok else danger("[error]")
        print(f"{styled_marker} Schema: {result['schema_revision']}")
        if diagnostics.schema_issues:
            for issue in diagnostics.schema_issues:
                print(danger(f"        {issue}"))
        _print_config_check("user.name", result["user.name"])
        _print_config_check("user.email", result["user.email"])
    return result


def _print_config_check(key: str, state: str) -> None:
    marker = success("[ok]") if state == "configured" else warning("[warn]")
    print(f"{marker} {key}: {state}")


def handle_completion(
    args: argparse.Namespace,
    _service: object,
) -> dict[str, str]:
    script = _completion_script(args.shell)
    if not args.json:
        print(script)
    return {"shell": args.shell, "script": script}


def _completion_script(shell: str) -> str:
    if shell == "bash":
        return _bash_completion()
    if shell == "zsh":
        return _zsh_completion()
    return _fish_completion()


def _bash_completion() -> str:
    cases = "\n".join(
        f'        {group}) candidates="{commands} --json --debug --color" ;;'
        for group, commands in _GROUP_COMMANDS.items()
    )
    return f"""_tk_completion() {{
    local current="${{COMP_WORDS[COMP_CWORD]}}"
    local candidates="{_ROOT_COMMANDS}"
    if (( COMP_CWORD > 1 )); then
        case "${{COMP_WORDS[1]}}" in
{cases}
        esac
    fi
    COMPREPLY=( $(compgen -W "$candidates" -- "$current") )
}}
complete -F _tk_completion tk"""


def _zsh_completion() -> str:
    cases = "\n".join(
        f"        {group}) _values 'command' {commands} --json --debug --color ;;"
        for group, commands in _GROUP_COMMANDS.items()
    )
    return f"""#compdef tk
_tk() {{
    if (( CURRENT == 2 )); then
        _values 'command' {_ROOT_COMMANDS}
        return
    fi
    case "$words[2]" in
{cases}
    esac
}}
compdef _tk tk"""


def _fish_completion() -> str:
    lines = [
        "complete -c tk -f",
        f"complete -c tk -n '__fish_use_subcommand' -a '{_ROOT_COMMANDS}'",
    ]
    lines.extend(
        f"complete -c tk -n '__fish_seen_subcommand_from {group}' -a '{commands}'"
        for group, commands in _GROUP_COMMANDS.items()
    )
    return "\n".join(lines)
