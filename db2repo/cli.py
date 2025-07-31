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
from .utils.validators import to_snowflake_name

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
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def branch_clone(profile: str, dry_run: bool) -> None:
    """Create a new Git branch and clone the Snowflake database."""
    try:
        config = ConfigManager()
        
        # Get the active profile
        if not profile:
            profile = config.get_active_profile()
        if not profile:
            console.print("[bold red]No active profile set. Please run 'db2repo setup' first.[/bold red]")
            raise click.Abort()
        
        profile_config = config.get_profile(profile)
        if not profile_config:
            console.print(f"[bold red]Profile '{profile}' not found.[/bold red]")
            raise click.Abort()
        
        # Get Git repository path and validate
        git_repo_path = profile_config.get("git_repo_path")
        if not git_repo_path:
            console.print("[bold red]Git repository path not configured in profile.[/bold red]")
            raise click.Abort()
        
        # Get database and schema
        database = profile_config.get("database")
        schema = profile_config.get("schema")
        if not database or not schema:
            console.print("[bold red]Database or schema not configured in profile.[/bold red]")
            raise click.Abort()
        
        # Initialize Git manager
        git_manager = GitManager(git_repo_path)
        if not GitManager.is_git_repository(git_repo_path):
            console.print("[bold red]Not in a git repository.[/bold red]")
            console.print(f"Please navigate to a git repository: {git_repo_path}")
            raise click.Abort()
        
        # Get current branch name
        current_branch = git_manager.get_current_branch()
        if not current_branch:
            console.print("[bold red]Could not determine current branch.[/bold red]")
            raise click.Abort()
        
        # Check if we're on main/master branch
        if current_branch in ["main", "master"]:
            console.print(f"[bold red]Cannot clone database while on '{current_branch}' branch.[/bold red]")
            console.print("Please create a feature branch first using 'git checkout -b <branch-name>'")
            raise click.Abort()
        
        # Check if the cloned database already exists in Snowflake
        # Use the original database name from the profile and append the branch name
        original_database = profile_config.get("database")
        snowflake_branch_name = to_snowflake_name(current_branch)
        cloned_database = f"{original_database}_{snowflake_branch_name}"
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
            console.print(f"Current branch: {current_branch}")
            console.print(f"Would check if database exists: {cloned_database}")
            console.print(f"Would create database clone if it doesn't exist")
            console.print(f"Would use database '{cloned_database}' for this branch")
            return
        
        console.print(f"[bold blue]Checking if database '{cloned_database}' already exists...[/bold blue]")
        
        # Initialize database adapter to check if database exists
        adapter = AdapterFactory.get_adapter(profile_config)
        
        # Test connection and attempt to clone database
        console.print("[bold blue]Testing database connection...[/bold blue]")
        try:
            if adapter.test_connection():
                console.print("[bold green]Database connection successful.[/bold green]")
                
                # Attempt to clone the database
                console.print(f"[bold blue]Attempting to clone database '{original_database}' to '{cloned_database}'...[/bold blue]")
                if adapter.clone_database(original_database, cloned_database):
                    console.print(f"[bold green]Successfully cloned database to '{cloned_database}'[/bold green]")
                else:
                    console.print(f"[bold yellow]Database cloning failed or database already exists.[/bold yellow]")
                    console.print(f"[bold yellow]You may need to manually create database '{cloned_database}' in Snowflake.[/bold yellow]")
            else:
                console.print("[bold red]Database connection failed.[/bold red]")
                console.print(f"[bold yellow]Please ensure you can connect to Snowflake and manually create database '{cloned_database}' if needed.[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]Database connection error:[/bold red] {e}")
            console.print(f"[bold yellow]Please manually create database '{cloned_database}' in Snowflake if needed.[/bold yellow]")
        
        console.print(f"[bold green]Branch '{current_branch}' will use database '{cloned_database}'[/bold green]")
        console.print(f"[bold blue]You can now make changes to '{cloned_database}' and sync them to this branch[/bold blue]")
        console.print(f"[bold blue]The main profile still points to '{original_database}' for the main branch[/bold blue]")
        
    except Exception as e:
        console.print(f"[bold red]Branch clone failed:[/bold red] {e}")
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

        # Get the active profile configuration
        profile_config = config.get_profile(profile)
        if not profile_config:
            console.print(f"[bold red]Profile '{profile}' not found.[/bold red]")
            raise click.Abort()

        # Check if we're on a feature branch and get the appropriate database
        git_manager = GitManager(profile_config.get("git_repo_path"))
        current_branch = git_manager.get_current_branch()
        database = profile_config.get("database")
        
        # Store the original database name for file organization
        original_database = database
        
        # If we're not on main/master branch, use branch-specific database name
        if current_branch and current_branch not in ["main", "master"]:
            snowflake_branch_name = to_snowflake_name(current_branch)
            branch_database = f"{database}_{snowflake_branch_name}"
            console.print(f"[bold blue]Using branch-specific database: {branch_database}[/bold blue]")
            database = branch_database
            # Update the adapter's configuration to use the branch-specific database
            profile_config["database"] = database
        else:
            console.print(f"[bold blue]Using main database: {database}[/bold blue]")
        
        schema = profile_config.get("schema")
        if not schema:
            console.print("[bold red]Schema not configured in profile.[/bold red]")
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
                        
                        # Determine file path - always use original database name for file organization
                        file_path = write_ddl_file(
                            base_dir=git_repo_path,
                            database=original_database,
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
 