"""Top-level argument parser assembly."""

import argparse

from termkeeper import __version__
from termkeeper.presentation.cli.parser_builders.admin import add_admin_commands, add_data_commands
from termkeeper.presentation.cli.parser_builders.common import (
    Commands,
    HelpFormatter,
    add_runtime_options,
)
from termkeeper.presentation.cli.parser_builders.meaning import add_meaning_commands
from termkeeper.presentation.cli.parser_builders.metadata import (
    add_reference_commands,
    add_scope_commands,
    add_tag_commands,
)
from termkeeper.presentation.cli.parser_builders.occurrence import add_occurrence_commands
from termkeeper.presentation.cli.parser_builders.primary import add_primary_commands


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tk",
        description=(
            "Capture unfamiliar terms, organize their meanings by scope, "
            "and find them later."
        ),
        epilog=(
            "Everyday workflow:\n"
            "  tk add TERM          Capture a term as encountered\n"
            "  tk inbox             Review unresolved occurrences\n"
            "  tk list              Browse known meanings\n"
            "  tk search QUERY      Find a meaning\n"
            "  tk resolve ID        Classify an occurrence\n"
            "\n"
            "Management:\n"
            "  tk occurrence --help   Occurrence history and state\n"
            "  tk meaning --help      Meaning lifecycle and relationships\n"
            "  tk scope --help        Meaning namespaces\n"
            "  tk tag --help          Tags\n"
            "  tk reference --help    Reference URLs\n"
            "\n"
            "System and data:\n"
            "  tk data --help         Import and export\n"
            "  tk config --help       User configuration\n"
            "  tk doctor              Diagnose the environment\n"
            "\n"
            "Run 'tk COMMAND --help' for command-specific options and examples."
        ),
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    add_runtime_options(parser)
    parser.set_defaults(command="dashboard")
    commands = Commands(parser, dest="root_command", required=False)
    init = commands.add("init", "Initialize or migrate the database", handler="init")
    init.add_argument(
        "--reset",
        action="store_true",
        help="Back up and recreate the configured SQLite database",
    )
    init.add_argument(
        "--yes",
        action="store_true",
        help="Confirm reset without prompting",
    )
    add_primary_commands(commands)
    add_occurrence_commands(commands.group("occurrence", "Manage occurrence history"))
    add_meaning_commands(commands.group("meaning", "Manage meanings"))
    add_tag_commands(commands.group("tag", "Manage meaning tags"))
    add_reference_commands(commands.group("reference", "Manage reference URLs"))
    add_scope_commands(commands.group("scope", "Manage meaning scopes"))
    add_data_commands(commands.group("data", "Import and export TermKeeper data"))
    add_admin_commands(commands)
    return parser
