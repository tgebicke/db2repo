"""
Main CLI module for DB2Repo.

This module contains the Click CLI group and all command definitions.
"""

import click
from rich.console import Console
from rich.text import Text

from . import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="db2repo")
def cli() -> None:
    """
    DB2Repo - Database DDL to Git Repository Tool

    A command-line interface tool for tracking database DDL (Data Definition Language)
    in a git repository. Supports multiple database platforms with an extensible
    adapter pattern, starting with Snowflake.
    """
    pass


@cli.command()
def version() -> None:
    """Show version information."""
    version_text = Text(f"DB2Repo version {__version__}", style="bold blue")
    console.print(version_text)


@cli.command()
def help() -> None:
    """Show detailed help information."""
    console.print("DB2Repo - Database DDL to Git Repository Tool", style="bold")
    console.print(
        "\nThis tool helps you track database DDL changes in git repositories."
    )
    console.print("\nFor more information, run: db2repo --help")
