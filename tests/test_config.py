"""
Tests for configuration management module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import toml

from db2repo.config import ConfigManager
from db2repo.exceptions import ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.toml"
        self.config_manager = ConfigManager(str(self.config_path))

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.config_path.exists():
            self.config_path.unlink()
        if self.temp_dir and os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_init_with_default_path(self):
        """Test initialization with default config path."""
        with patch("os.path.expanduser", return_value="/home/user/.db2repo.toml"):
            config = ConfigManager()
            assert str(config.config_path) == "/home/user/.db2repo.toml"

    def test_init_with_custom_path(self):
        """Test initialization with custom config path."""
        custom_path = "/custom/path/config.toml"
        config = ConfigManager(custom_path)
        assert str(config.config_path) == custom_path

    def test_load_config_new_file(self):
        """Test loading configuration from a new file."""
        assert self.config_manager._config == {}

    def test_load_config_existing_file(self):
        """Test loading configuration from an existing file."""
        test_config = {
            "active_profile": "dev",
            "dev": {"platform": "snowflake", "account": "test.snowflakecomputing.com"},
        }

        with open(self.config_path, "w") as f:
            toml.dump(test_config, f)

        config = ConfigManager(str(self.config_path))
        assert config._config == test_config

    def test_load_config_invalid_toml(self):
        """Test loading configuration with invalid TOML."""
        with open(self.config_path, "w") as f:
            f.write("invalid toml content [")

        with pytest.raises(ConfigurationError, match="Invalid TOML configuration file"):
            ConfigManager(str(self.config_path))

    def test_save_config(self):
        """Test saving configuration to file."""
        test_config = {"active_profile": "test"}
        self.config_manager._config = test_config
        self.config_manager._save_config()

        assert self.config_path.exists()
        with open(self.config_path, "r") as f:
            loaded_config = toml.load(f)
        assert loaded_config == test_config

    def test_get_active_profile(self):
        """Test getting active profile."""
        self.config_manager._config = {"active_profile": "dev"}
        assert self.config_manager.get_active_profile() == "dev"

    def test_get_active_profile_none(self):
        """Test getting active profile when none is set."""
        assert self.config_manager.get_active_profile() is None

    def test_set_active_profile(self):
        """Test setting active profile."""
        self.config_manager.set_active_profile("prod")
        assert self.config_manager.get_active_profile() == "prod"

    def test_get_profile(self):
        """Test getting a specific profile."""
        profile_config = {"platform": "snowflake", "account": "test.com"}
        self.config_manager._config = {"dev": profile_config}
        assert self.config_manager.get_profile("dev") == profile_config

    def test_get_profile_nonexistent(self):
        """Test getting a non-existent profile."""
        assert self.config_manager.get_profile("nonexistent") is None

    def test_set_profile_valid(self):
        """Test setting a valid profile."""
        profile_config = {
            "platform": "snowflake",
            "account": "test.snowflakecomputing.com",
            "username": "testuser",
            "database": "testdb",
            "schema": "public",
        }
        self.config_manager.set_profile("dev", profile_config)
        assert self.config_manager.get_profile("dev") == profile_config

    def test_set_profile_invalid_name(self):
        """Test setting profile with invalid name."""
        profile_config = {"platform": "snowflake"}
        with pytest.raises(
            ConfigurationError, match="Profile name must be a non-empty string"
        ):
            self.config_manager.set_profile("", profile_config)

    def test_set_profile_missing_platform(self):
        """Test setting profile without platform."""
        profile_config = {"account": "test.com"}
        with pytest.raises(
            ConfigurationError,
            match="Profile configuration missing required field: platform",
        ):
            self.config_manager.set_profile("dev", profile_config)

    def test_set_profile_invalid_platform(self):
        """Test setting profile with invalid platform."""
        profile_config = {"platform": ""}
        with pytest.raises(
            ConfigurationError, match="Platform must be a non-empty string"
        ):
            self.config_manager.set_profile("dev", profile_config)

    def test_set_snowflake_profile_missing_fields(self):
        """Test setting Snowflake profile with missing required fields."""
        profile_config = {"platform": "snowflake", "account": "test.com"}
        with pytest.raises(
            ConfigurationError,
            match="Snowflake profile missing required field: username",
        ):
            self.config_manager.set_profile("dev", profile_config)

    def test_list_profiles(self):
        """Test listing profiles."""
        self.config_manager._config = {
            "active_profile": "dev",
            "dev": {"platform": "snowflake"},
            "prod": {"platform": "snowflake"},
        }
        profiles = self.config_manager.list_profiles()
        assert profiles == ["dev", "prod"]

    def test_list_profiles_empty(self):
        """Test listing profiles when none exist."""
        profiles = self.config_manager.list_profiles()
        assert profiles == []

    def test_delete_profile(self):
        """Test deleting a profile."""
        self.config_manager._config = {
            "dev": {"platform": "snowflake"},
            "prod": {"platform": "snowflake"},
        }
        self.config_manager.delete_profile("dev")
        assert "dev" not in self.config_manager._config
        assert "prod" in self.config_manager._config

    def test_delete_profile_nonexistent(self):
        """Test deleting a non-existent profile."""
        with pytest.raises(
            ConfigurationError, match="Profile 'nonexistent' does not exist"
        ):
            self.config_manager.delete_profile("nonexistent")

    def test_delete_active_profile(self):
        """Test deleting the active profile."""
        self.config_manager._config = {
            "active_profile": "dev",
            "dev": {"platform": "snowflake"},
        }
        with pytest.raises(ConfigurationError, match="Cannot delete active profile"):
            self.config_manager.delete_profile("dev")

    def test_validate_profile_valid(self):
        """Test validating a valid profile."""
        profile_config = {
            "platform": "snowflake",
            "account": "test.snowflakecomputing.com",
            "username": "testuser",
            "database": "testdb",
            "schema": "public",
        }
        self.config_manager.set_profile("dev", profile_config)
        errors = self.config_manager.validate_profile("dev")
        assert errors == []

    def test_validate_profile_invalid(self):
        """Test validating an invalid profile."""
        profile_config = {"platform": "snowflake"}  # Missing required fields
        self.config_manager._config["dev"] = profile_config
        errors = self.config_manager.validate_profile("dev")
        assert len(errors) > 0
        assert "missing required field" in errors[0]

    def test_validate_profile_nonexistent(self):
        """Test validating a non-existent profile."""
        errors = self.config_manager.validate_profile("nonexistent")
        assert errors == ["Profile 'nonexistent' does not exist"]

    def test_get_active_profile_config(self):
        """Test getting active profile configuration."""
        profile_config = {"platform": "snowflake"}
        self.config_manager._config = {"active_profile": "dev", "dev": profile_config}
        assert self.config_manager.get_active_profile_config() == profile_config

    def test_get_active_profile_config_none(self):
        """Test getting active profile configuration when none is set."""
        assert self.config_manager.get_active_profile_config() is None

    def test_profile_exists(self):
        """Test checking if profile exists."""
        self.config_manager._config = {"dev": {"platform": "snowflake"}}
        assert self.config_manager.profile_exists("dev") is True
        assert self.config_manager.profile_exists("nonexistent") is False

    def test_get_profile_count(self):
        """Test getting profile count."""
        self.config_manager._config = {
            "dev": {"platform": "snowflake"},
            "prod": {"platform": "snowflake"},
        }
        assert self.config_manager.get_profile_count() == 2

    def test_get_config_path(self):
        """Test getting config path."""
        assert self.config_manager.get_config_path() == str(self.config_path)
