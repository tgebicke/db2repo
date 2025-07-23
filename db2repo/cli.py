"""
Main CLI module for DB2Repo.

This module contains the Click CLI group and all command definitions.
"""

import click
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .config import ConfigManager
from .exceptions import ConfigurationError

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


@cli.group()
def profiles() -> None:
    """Manage database profiles."""
    pass


@profiles.command()
def list() -> None:
    """List all available profiles."""
    try:
        config = ConfigManager()
        profile_list = config.list_profiles()
        active_profile = config.get_active_profile()

        if not profile_list:
            console.print("No profiles configured.", style="yellow")
            console.print("Use 'db2repo setup' to create your first profile.")
            return

        table = Table(title="Database Profiles")
        table.add_column("Profile Name", style="cyan", no_wrap=True)
        table.add_column("Platform", style="green")
        table.add_column("Database", style="blue")
        table.add_column("Schema", style="magenta")
        table.add_column("Status", style="bold")

        for profile_name in profile_list:
            profile = config.get_profile(profile_name)
            platform = profile.get("platform", "unknown")
            database = profile.get("database", "N/A")
            schema = profile.get("schema", "N/A")

            status = "ACTIVE" if profile_name == active_profile else ""
            status_style = "bold green" if status else ""

            table.add_row(
                profile_name, platform, database, schema, status, style=status_style
            )

        console.print(table)

        if active_profile:
            console.print(
                f"\nActive profile: [bold green]{active_profile}[/bold green]"
            )
        else:
            console.print("\n[bold yellow]No active profile set.[/bold yellow]")
            console.print("Use 'db2repo use-profile <name>' to set an active profile.")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


@profiles.command()
@click.argument("profile_name")
def use(profile_name: str) -> None:
    """Set the active profile."""
    try:
        config = ConfigManager()

        if not config.profile_exists(profile_name):
            console.print(
                f"[bold red]Profile '{profile_name}' does not exist.[/bold red]"
            )
            console.print("Available profiles:")
            for p in config.list_profiles():
                console.print(f"  - {p}")
            raise click.Abort()

        config.set_active_profile(profile_name)
        console.print(f"[bold green]Active profile set to:[/bold green] {profile_name}")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


@profiles.command()
@click.argument("profile_name")
def delete(profile_name: str) -> None:
    """Delete a profile."""
    try:
        config = ConfigManager()

        if not config.profile_exists(profile_name):
            console.print(
                f"[bold red]Profile '{profile_name}' does not exist.[/bold red]"
            )
            raise click.Abort()

        # Confirm deletion
        if not click.confirm(
            f"Are you sure you want to delete profile '{profile_name}'?"
        ):
            console.print("Profile deletion cancelled.")
            return

        config.delete_profile(profile_name)
        console.print(
            f"[bold green]Profile '{profile_name}' deleted successfully.[/bold green]"
        )

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.option("--profile", "-p", help="Profile name to create/edit")
def setup(profile: str) -> None:
    """Set up a new database profile (interactive)."""
    try:
        config = ConfigManager()

        # Get profile name
        if not profile:
            profile = click.prompt("Enter profile name", default="default")

        # Check if profile exists
        if config.profile_exists(profile):
            if not click.confirm(
                f"Profile '{profile}' already exists. Do you want to update it?"
            ):
                console.print("Setup cancelled.")
                return

        console.print(f"\n[bold]Setting up profile:[/bold] {profile}")
        console.print("=" * 50)

        # Platform selection
        platform = click.prompt(
            "Select database platform",
            type=click.Choice(["snowflake"], case_sensitive=False),
            default="snowflake",
        ).lower()

        # Platform-specific setup
        if platform == "snowflake":
            profile_config = _setup_snowflake_profile()
        else:
            console.print(
                f"[bold red]Platform '{platform}' not yet supported.[/bold red]"
            )
            raise click.Abort()

        # Git repository configuration
        console.print("\n[bold]Git Repository Configuration[/bold]")
        console.print("-" * 30)

        git_repo_path = click.prompt("Git repository path", default="~/ddl-repository")

        git_remote_url = click.prompt("Git remote URL (optional)", default="")

        git_branch = click.prompt("Git branch", default="main")

        git_author_name = click.prompt("Git author name", default="DB2Repo User")

        git_author_email = click.prompt(
            "Git author email", default="db2repo@example.com"
        )

        # Add git configuration to profile
        profile_config.update(
            {
                "git_repo_path": git_repo_path,
                "git_remote_url": git_remote_url,
                "git_branch": git_branch,
                "git_author_name": git_author_name,
                "git_author_email": git_author_email,
            }
        )

        # Save profile
        config.set_profile(profile, profile_config)

        # Set as active if it's the first profile
        if config.get_profile_count() == 1:
            config.set_active_profile(profile)
            console.print(
                f"\n[bold green]Profile '{profile}' created and set as active.[/bold green]"
            )
        else:
            if click.confirm(f"Set '{profile}' as the active profile?"):
                config.set_active_profile(profile)
                console.print(
                    f"\n[bold green]Profile '{profile}' created and set as active.[/bold green]"
                )
            else:
                console.print(
                    f"\n[bold green]Profile '{profile}' created successfully.[/bold green]"
                )

        console.print(
            f"\nConfiguration saved to: [cyan]{config.get_config_path()}[/cyan]"
        )

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


def _setup_snowflake_profile() -> dict:
    """Interactive setup for Snowflake profile."""
    console.print("\n[bold]Snowflake Configuration[/bold]")
    console.print("-" * 25)

    account = click.prompt("Snowflake account URL")
    username = click.prompt("Username")

    # Authentication method
    auth_method = click.prompt(
        "Authentication method",
        type=click.Choice(
            ["username_password", "ssh_key", "external_browser"], case_sensitive=False
        ),
        default="username_password",
    ).lower()

    profile_config = {
        "platform": "snowflake",
        "account": account,
        "username": username,
        "auth_method": auth_method,
    }

    if auth_method == "username_password":
        password = click.prompt("Password", hide_input=True)
        profile_config["password"] = password
    elif auth_method == "ssh_key":
        private_key_path = click.prompt(
            "Private key path", default="~/.ssh/snowflake_key"
        )
        profile_config["private_key_path"] = private_key_path

    warehouse = click.prompt("Warehouse", default="")
    database = click.prompt("Database")
    schema = click.prompt("Schema", default="public")
    role = click.prompt("Role (optional)", default="")

    if warehouse:
        profile_config["warehouse"] = warehouse
    if role:
        profile_config["role"] = role

    profile_config.update(
        {
            "database": database,
            "schema": schema,
        }
    )

    return profile_config
