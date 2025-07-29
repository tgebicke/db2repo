"""
Tests for profile management CLI commands.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import click
import pytest
from click.testing import CliRunner

from db2repo.cli import cli
from db2repo.config import ConfigManager


class TestProfileCommands:
    """Test cases for profile management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.toml"
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.config_path.exists():
            self.config_path.unlink()
        if self.temp_dir and Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_list_empty(self, mock_config_manager):
        """Test listing profiles when none exist."""
        mock_config = MagicMock()
        mock_config.list_profiles.return_value = []
        mock_config.get_active_profile.return_value = None
        mock_config_manager.return_value = mock_config
    
        result = self.runner.invoke(cli, ["profiles", "list"])
    
        assert result.exit_code == 0
        assert "No profiles configured" in result.output
        assert "Use 'db2repo setup'" in result.output

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_list_with_profiles(self, mock_config_manager):
        """Test listing profiles when profiles exist."""
        mock_config = MagicMock()
        mock_config.list_profiles.return_value = ["dev", "prod"]
        mock_config.get_active_profile.return_value = "dev"
        mock_config.get_profile.side_effect = lambda name: {
            "dev": {"platform": "snowflake", "database": "devdb", "schema": "public"},
            "prod": {"platform": "snowflake", "database": "proddb", "schema": "prod"},
        }.get(name)
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(cli, ["profiles", "list"])

        assert result.exit_code == 0
        assert "dev" in result.output
        assert "prod" in result.output
        assert "ACTIVE" in result.output

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_use_existing(self, mock_config_manager):
        """Test setting active profile to existing profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = True
        mock_config.list_profiles.return_value = ["dev", "prod"]
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(cli, ["profiles", "use", "dev"])

        assert result.exit_code == 0
        assert "Active profile set to: dev" in result.output
        mock_config.set_active_profile.assert_called_once_with("dev")

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_use_nonexistent(self, mock_config_manager):
        """Test setting active profile to non-existent profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config.list_profiles.return_value = ["dev", "prod"]
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(cli, ["profiles", "use", "nonexistent"])

        assert result.exit_code != 0
        assert "Profile 'nonexistent' does not exist" in result.output

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_delete_existing(self, mock_config_manager):
        """Test deleting an existing profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = True
        mock_config_manager.return_value = mock_config
    
        result = self.runner.invoke(cli, ["profiles", "delete", "dev"], input="y\n")
    
        assert result.exit_code == 0
        assert "Profile 'dev' deleted." in result.output
        mock_config.delete_profile.assert_called_once_with("dev")

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_delete_nonexistent(self, mock_config_manager):
        """Test deleting a non-existent profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(cli, ["profiles", "delete", "nonexistent"])

        assert result.exit_code != 0
        assert "Profile 'nonexistent' does not exist" in result.output

    @patch("db2repo.cli.ConfigManager")
    def test_profiles_delete_cancelled(self, mock_config_manager):
        """Test cancelling profile deletion."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = True
        mock_config_manager.return_value = mock_config

        result = self.runner.invoke(cli, ["profiles", "delete", "dev"], input="n\n")

        assert result.exit_code == 0
        assert "Profile deletion cancelled" in result.output
        mock_config.delete_profile.assert_not_called()


class TestSetupCommand:
    """Test cases for the setup command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("db2repo.cli.ConfigManager")
    @patch("click.prompt")
    @patch("click.confirm")
    def test_setup_new_profile(self, mock_confirm, mock_prompt, mock_config_manager):
        """Test setting up a new profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config.get_profile_count.return_value = 0
        mock_config_manager.return_value = mock_config

        # Mock all the prompts
        mock_prompt.side_effect = [
            "default",  # profile name
            "snowflake",  # platform
            "test.snowflakecomputing.com",  # account
            "testuser",  # username
            "username_password",  # auth method
            "password123",  # password
            "",  # warehouse (empty)
            "testdb",  # database
            "public",  # schema
            "",  # role (empty)
            "~/ddl-repo",  # git repo path
            "",  # git remote url
            "main",  # git branch
            "Test User",  # git author name
            "test@example.com",  # git author email
        ]
        mock_confirm.return_value = True  # Set as active

        result = self.runner.invoke(cli, ["setup"])

        assert result.exit_code == 0
        assert "Profile 'default' created and set as active" in result.output
        mock_config.set_profile.assert_called_once()
        mock_config.set_active_profile.assert_called_once_with("default")

    @patch("db2repo.cli.ConfigManager")
    @patch("click.prompt")
    @patch("click.confirm")
    def test_setup_existing_profile_update(
        self, mock_confirm, mock_prompt, mock_config_manager
    ):
        """Test updating an existing profile."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = True
        mock_config.get_profile_count.return_value = 1
        mock_config_manager.return_value = mock_config

        # Mock confirmations
        mock_confirm.side_effect = [True, True]  # Update profile, set as active

        # Mock all the prompts
        mock_prompt.side_effect = [
            "snowflake",  # platform
            "test.snowflakecomputing.com",  # account
            "testuser",  # username
            "username_password",  # auth method
            "password123",  # password
            "",  # warehouse (empty)
            "testdb",  # database
            "public",  # schema
            "",  # role (empty)
            "~/ddl-repo",  # git repo path
            "",  # git remote url
            "main",  # git branch
            "Test User",  # git author name
            "test@example.com",  # git author email
        ]

        result = self.runner.invoke(cli, ["setup", "--profile", "existing"])

        assert result.exit_code == 0
        assert "Profile 'existing' created and set as active" in result.output

    @patch("db2repo.cli.ConfigManager")
    @patch("click.confirm")
    def test_setup_existing_profile_cancel(self, mock_confirm, mock_config_manager):
        """Test cancelling setup when profile exists."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = True
        mock_config_manager.return_value = mock_config

        mock_confirm.return_value = False  # Don't update

        result = self.runner.invoke(cli, ["setup", "--profile", "existing"])

        assert result.exit_code == 0
        assert "Setup cancelled" in result.output
        mock_config.set_profile.assert_not_called()

    @patch("db2repo.cli.GitManager")
    @patch("db2repo.cli.ConfigManager")
    @patch("click.prompt")
    @patch("click.confirm")
    def test_setup_git_repo_init(
        self, mock_confirm, mock_prompt, mock_config_manager, mock_git_manager
    ):
        """Test setup initializes a new git repository if not present."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config.get_profile_count.return_value = 0
        mock_config_manager.return_value = mock_config
        mock_git_manager.is_git_repository.return_value = False
        mock_git_manager.initialize_repository.return_value = True

        # Mock all the prompts
        mock_prompt.side_effect = [
            "default",  # profile name
            "snowflake",  # platform
            "test.snowflakecomputing.com",  # account
            "testuser",  # username
            "username_password",  # auth method
            "password123",  # password
            "",  # warehouse (empty)
            "testdb",  # database
            "public",  # schema
            "",  # role (empty)
            "~/ddl-repo",  # git repo path
            "",  # git remote url
            "main",  # git branch
            "Test User",  # git author name
            "test@example.com",  # git author email
        ]
        mock_confirm.side_effect = [True, True]  # Initialize git repo, set as active

        runner = CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert "Initialized new git repository" in result.output
        mock_git_manager.initialize_repository.assert_called_once()

    @patch("db2repo.cli.GitManager")
    @patch("db2repo.cli.ConfigManager")
    @patch("click.prompt")
    @patch("click.confirm")
    def test_setup_git_repo_cancel(
        self, mock_confirm, mock_prompt, mock_config_manager, mock_git_manager
    ):
        """Test setup cancels if user declines to initialize git repo."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config.get_profile_count.return_value = 0
        mock_config_manager.return_value = mock_config
        mock_git_manager.is_git_repository.return_value = False
    
        # Mock all the prompts
        mock_prompt.side_effect = [
            "default",  # profile name
            "snowflake",  # platform
            "test.snowflakecomputing.com",  # account
            "testuser",  # username
            "username_password",  # auth method
            "password123",  # password
            "",  # warehouse (empty)
            "testdb",  # database
            "public",  # schema
            "",  # role (empty)
            "~/ddl-repo",  # git repo path
            "",  # git remote url
            "main",  # git branch
            "Test User",  # git author name
            "test@example.com",  # git author email
        ]
        mock_confirm.side_effect = [False]  # Decline to initialize git repo
    
        runner = CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code != 0
        assert (
            "Please clone the repository manually and rerun setup."
            in result.output
        )

    @patch("db2repo.cli.GitManager")
    @patch("db2repo.cli.ConfigManager")
    @patch("click.prompt")
    @patch("click.confirm")
    def test_setup_git_repo_with_remote_url(
        self, mock_confirm, mock_prompt, mock_config_manager, mock_git_manager
    ):
        """Test setup aborts if path is not a git repo and remote URL is provided."""
        mock_config = MagicMock()
        mock_config.profile_exists.return_value = False
        mock_config.get_profile_count.return_value = 0
        mock_config_manager.return_value = mock_config
        mock_git_manager.is_git_repository.return_value = False
    
        # Mock all the prompts
        mock_prompt.side_effect = [
            "default",  # profile name
            "snowflake",  # platform
            "test.snowflakecomputing.com",  # account
            "testuser",  # username
            "username_password",  # auth method
            "password123",  # password
            "",  # warehouse (empty)
            "testdb",  # database
            "public",  # schema
            "",  # role (empty)
            "~/ddl-repo",  # git repo path
            "https://github.com/example/repo.git",  # git remote url
            "main",  # git branch
            "Test User",  # git author name
            "test@example.com",  # git author email
        ]
        mock_confirm.side_effect = [False]  # Decline to initialize git repo
    
        runner = CliRunner()
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code != 0
        assert "Please clone the repository manually and rerun setup." in result.output
