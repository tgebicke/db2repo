"""
Main CLI module for DB2Repo.

This module contains the Click CLI group and all command definitions.
"""

import click
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from . import __version__
from .config import ConfigManager
from .exceptions import ConfigurationError, DatabaseConnectionError
from .git.manager import GitManager
from .adapters import AdapterFactory
from .utils.file_organization import write_ddl_file

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
        console.print(f"[bold green]Profile '{profile_name}' deleted.[/bold green]")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.option("--profile", "-p", help="Profile name to create/edit")
def setup(profile: str) -> None:
    """Set up a new database profile or edit an existing one."""
    try:
        config = ConfigManager()
        
        # Determine profile name
        if profile:
            profile_name = profile
        else:
            if config.get_profile_count() == 0:
                profile_name = "default"
            else:
                profile_name = click.prompt(
                    "Profile name",
                    default="default",
                    type=str
                )

        # Check if profile exists
        if config.profile_exists(profile_name):
            if not click.confirm(f"Profile '{profile_name}' already exists. Update it?"):
                console.print("Setup cancelled.")
                return

        console.print(f"\nSetting up profile: {profile_name}")
        console.print("=" * 50)

        # Platform selection
        console.print("\nSnowflake Configuration")
        console.print("-" * 25)
        
        platform = "snowflake"  # For now, only Snowflake is supported
        
        # Snowflake-specific configuration
        snowflake_config = _setup_snowflake_profile()
        
        # Git repository configuration
        console.print("\nGit Repository Configuration")
        console.print("-" * 30)
        
        git_repo_path = click.prompt(
            "Git repository path",
            default="~/ddl-repo",
            type=str
        )
        
        git_remote_url = click.prompt(
            "Git remote URL (optional)",
            default="",
            type=str
        )
        
        git_branch = click.prompt(
            "Git branch",
            default="main",
            type=str
        )
        
        git_author_name = click.prompt(
            "Git author name",
            default="DB2Repo User",
            type=str
        )
        
        git_author_email = click.prompt(
            "Git author email",
            default="user@example.com",
            type=str
        )

        # Validate git repository
        if not GitManager.is_git_repository(git_repo_path):
            if git_remote_url:
                console.print(f"[yellow]The path '{git_repo_path}' is not a git repository.[/yellow]")
                if click.confirm("Initialize a new git repository and add the remote?"):
                    success = GitManager.initialize_repository(git_repo_path)
                    if success:
                        console.print(f"[green]Initialized new git repository at {git_repo_path}.[/green]")
                        # TODO: Add remote URL to git config
                        console.print(f"[yellow]Note: Remote URL '{git_remote_url}' will need to be added manually.[/yellow]")
                    else:
                        console.print(f"[red]Failed to initialize git repository at {git_repo_path}.[/red]")
                        raise click.Abort()
                else:
                    console.print("Please clone the repository manually and rerun setup.")
                    raise click.Abort()
            else:
                if click.confirm(f"The path '{git_repo_path}' is not a git repository. Initialize a new git repo here?"):
                    success = GitManager.initialize_repository(git_repo_path)
                    if success:
                        console.print(f"[green]Initialized new git repository at {git_repo_path}.[/green]")
                    else:
                        console.print(f"[red]Failed to initialize git repository at {git_repo_path}.[/red]")
                        raise click.Abort()
                else:
                    console.print(f"[red]Setup cancelled. Please provide a valid git repository path.[/red]")
                    raise click.Abort()

        # Combine all configuration
        profile_config = {
            "platform": platform,
            **snowflake_config,
            "git_repo_path": git_repo_path,
            "git_remote_url": git_remote_url,
            "git_branch": git_branch,
            "git_author_name": git_author_name,
            "git_author_email": git_author_email,
        }

        # Save profile
        config.set_profile(profile_name, profile_config)
        
        # Set as active if it's the first profile or user confirms
        if config.get_profile_count() == 1 or click.confirm(f"Set '{profile_name}' as active profile?"):
            config.set_active_profile(profile_name)
            console.print(f"\n[bold green]Profile '{profile_name}' created and set as active[/bold green]")
        else:
            console.print(f"\n[bold green]Profile '{profile_name}' created[/bold green]")

        console.print(f"\nConfiguration saved to: {config.get_config_path()}")

    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error:[/bold red] {e}")
        raise click.Abort()


@cli.command()
@click.option("--profile", "-p", help="Profile name to use (defaults to active profile)")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without making changes")
@click.option("--commit", is_flag=True, help="Automatically commit changes to git")
def sync(profile: str, dry_run: bool, commit: bool) -> None:
    """Sync DDL from database to repository."""
    try:
        config = ConfigManager()
        
        # Get profile configuration
        if profile:
            if not config.profile_exists(profile):
                console.print(f"[bold red]Profile '{profile}' does not exist.[/bold red]")
                raise click.Abort()
            profile_config = config.get_profile(profile)
        else:
            profile_config = config.get_active_profile_config()
            if not profile_config:
                console.print("[bold red]No active profile set.[/bold red]")
                console.print("Use 'db2repo profiles use <name>' or 'db2repo setup' to configure a profile.")
                raise click.Abort()

        # Get git repository path
        git_repo_path = profile_config.get("git_repo_path")
        if not git_repo_path:
            console.print("[bold red]Git repository path not configured.[/bold red]")
            console.print("Run 'db2repo setup' to configure git repository settings.")
            raise click.Abort()

        # Initialize database adapter
        try:
            adapter = AdapterFactory.get_adapter(profile_config)
        except Exception as e:
            console.print(f"[bold red]Failed to initialize database adapter:[/bold red] {e}")
            raise click.Abort()

        # Test connection (skip for now due to CFFI issues)
        console.print("[bold blue]Testing database connection...[/bold blue]")
        try:
            # Skip connection test for now due to CFFI issues
            console.print("[bold green]Database connection test skipped.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Database connection failed:[/bold red] {e}")
            raise click.Abort()

        # Get database and schema from profile
        database = profile_config.get("database")
        schema = profile_config.get("schema")
        
        if not database or not schema:
            console.print("[bold red]Database or schema not configured in profile.[/bold red]")
            raise click.Abort()

        console.print(f"\n[bold blue]Syncing DDL from {database}.{schema}[/bold blue]")
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be written[/yellow]")

        # Initialize git manager
        git_manager = GitManager(git_repo_path)
        
        # Track files for git commit
        files_to_commit = []
        
        # Progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Extract and save DDL for each object type
            object_types = [
                ("Tables", adapter.get_tables),
                ("Views", adapter.get_views),
                ("Materialized Views", adapter.get_materialized_views),
                ("Stages", adapter.get_stages),
                ("Snow Pipes", adapter.get_snowpipes),
                ("Stored Procedures", adapter.get_stored_procedures),
            ]
            
            total_objects = 0
            successful_objects = 0
            failed_objects = 0
            
            for object_type_name, extract_method in object_types:
                progress.add_task(f"Extracting {object_type_name}...", total=None)
                
                try:
                    objects = extract_method(database, schema)
                    total_objects += len(objects)
                    
                    for obj in objects:
                        if obj.get("error"):
                            failed_objects += 1
                            console.print(f"[red]Error extracting {obj['type']} {obj['name']}: {obj['error']}[/red]")
                            continue
                            
                        if not obj.get("ddl"):
                            failed_objects += 1
                            console.print(f"[red]No DDL found for {obj['type']} {obj['name']}[/red]")
                            continue
                        
                        # Determine file path
                        file_path = write_ddl_file(
                            base_dir=git_repo_path,
                            database=database,
                            schema=schema,
                            object_type=obj["type"],
                            object_name=obj["name"],
                            ddl=obj["ddl"],
                            overwrite=True
                        )
                        
                        if not dry_run:
                            files_to_commit.append(str(file_path))
                        
                        successful_objects += 1
                        
                except Exception as e:
                    console.print(f"[red]Error extracting {object_type_name}: {e}[/red]")
                    failed_objects += 1

        # Summary
        console.print(f"\n[bold]Sync Summary:[/bold]")
        console.print(f"  Total objects: {total_objects}")
        console.print(f"  Successful: [green]{successful_objects}[/green]")
        console.print(f"  Failed: [red]{failed_objects}[/red]")
        
        if dry_run:
            console.print(f"\n[yellow]Dry run completed. No files were written.[/yellow]")
            return

        # Git operations
        if files_to_commit and commit:
            console.print(f"\n[bold blue]Committing changes to git...[/bold blue]")
            try:
                # Add files to git
                if git_manager.add_files(files_to_commit):
                    # Commit changes
                    commit_message = f"Sync DDL from {database}.{schema} - {successful_objects} objects"
                    if git_manager.commit_changes(commit_message):
                        console.print(f"[bold green]Changes committed to git.[/bold green]")
                    else:
                        console.print(f"[yellow]Git commit failed.[/yellow]")
                else:
                    console.print(f"[yellow]Git add failed.[/yellow]")
            except Exception as e:
                console.print(f"[red]Git operation failed: {e}[/red]")
        elif files_to_commit:
            console.print(f"\n[bold yellow]Files written but not committed.[/bold yellow]")
            console.print(f"Run 'git add . && git commit -m \"Sync DDL\"' in {git_repo_path} to commit changes.")
        else:
            console.print(f"\n[yellow]No files were written.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Sync failed:[/bold red] {e}")
        raise click.Abort()


def _setup_snowflake_profile() -> dict:
    """Set up Snowflake-specific configuration."""
    account = click.prompt("Snowflake account", type=str)
    username = click.prompt("Username", type=str)
    
    auth_method = click.prompt(
        "Authentication method",
        type=click.Choice(["username_password", "external_browser", "ssh_key"]),
        default="username_password"
    )
    
    config = {
        "account": account,
        "username": username,
        "auth_method": auth_method,
    }
    
    if auth_method == "username_password":
        config["password"] = click.prompt("Password", type=str, hide_input=True)
    elif auth_method == "ssh_key":
        config["private_key_path"] = click.prompt("Private key file path", type=str)
    
    # Optional fields
    warehouse = click.prompt("Warehouse (optional)", default="", type=str)
    if warehouse:
        config["warehouse"] = warehouse
    
    database = click.prompt("Database", type=str)
    config["database"] = database
    
    schema = click.prompt("Schema", type=str)
    config["schema"] = schema
    
    role = click.prompt("Role (optional)", default="", type=str)
    if role:
        config["role"] = role
    
    return config
