"""
Tests for CLI module.
"""

import pytest
from click.testing import CliRunner

from db2repo.cli import cli


class TestCLI:
    """Test cases for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that CLI shows help."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "DB2Repo" in result.output

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(cli, ["help"])
        assert result.exit_code == 0
        assert "DB2Repo" in result.output
