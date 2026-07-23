"""Configuration and transfer command parsers."""

from termkeeper.presentation.cli.parser_builders.common import Commands


def add_config_and_transfer_commands(commands: Commands) -> None:
    config = commands.add(
        "config",
        "Get or set user configuration",
        handler="config",
        examples=(
            "Examples:\n"
            "  tk config user.name \"Taro Yamada\"\n"
            "  tk config user.email\n"
            "  tk config --list\n"
            "  tk config --unset user.email"
        ),
    )
    config.add_argument("key", nargs="?", choices=("user.name", "user.email"))
    config.add_argument("value", nargs="?")
    action = config.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true", dest="list_config")
    action.add_argument("--unset", action="store_true")
    export = commands.add("export", "Export meanings to CSV", handler="export")
    export.add_argument("path", nargs="?", default="termkeeper_export.csv")
    import_ = commands.add("import", "Import meanings from CSV", handler="import")
    import_.add_argument("path")
    import_.add_argument("--dry-run", action="store_true")
    import_.add_argument("--strict", action="store_true")
