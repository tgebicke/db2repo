"""
Configuration management module for DB2Repo.

This module handles loading, saving, and managing configuration files
in TOML format with profile-based settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml

from .exceptions import ConfigurationError


class ConfigManager:
    """Manages configuration files and profiles for DB2Repo."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to config file. Defaults to ~/.db2repo.toml
        """
        if config_path is None:
            config_path = os.path.expanduser("~/.db2repo.toml")

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                self._config = toml.load(self.config_path)
                self._validate_config_structure()
            except toml.TomlDecodeError as e:
                raise ConfigurationError(f"Invalid TOML configuration file: {e}")
        else:
            self._config = {}

    def _validate_config_structure(self) -> None:
        """Validate the basic structure of the configuration."""
        if not isinstance(self._config, dict):
            raise ConfigurationError("Configuration must be a dictionary")

        # Validate active_profile if it exists
        if "active_profile" in self._config:
            active_profile = self._config["active_profile"]
            if not isinstance(active_profile, str):
                raise ConfigurationError("active_profile must be a string")
            if active_profile and active_profile not in self._config:
                raise ConfigurationError(
                    f"Active profile '{active_profile}' does not exist"
                )

    def _save_config(self) -> None:
        """Save configuration to file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            toml.dump(self._config, f)

    def get_active_profile(self) -> Optional[str]:
        """Get the currently active profile name."""
        return self._config.get("active_profile")

    def set_active_profile(self, profile_name: str) -> None:
        """Set the active profile."""
        self._config["active_profile"] = profile_name
        self._save_config()

    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific profile."""
        return self._config.get(profile_name)

    def set_profile(self, profile_name: str, profile_config: Dict[str, Any]) -> None:
        """Set configuration for a specific profile."""
        if not profile_name or not isinstance(profile_name, str):
            raise ConfigurationError("Profile name must be a non-empty string")

        # Validate profile configuration
        self._validate_profile_config(profile_config)

        self._config[profile_name] = profile_config
        self._save_config()

    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        profiles = []
        for key in self._config.keys():
            if key != "active_profile":
                profiles.append(key)
        return sorted(profiles)

    def delete_profile(self, profile_name: str) -> None:
        """Delete a profile."""
        if profile_name not in self._config:
            raise ConfigurationError(f"Profile '{profile_name}' does not exist")

        # Don't allow deletion of the active profile
        if self.get_active_profile() == profile_name:
            raise ConfigurationError(
                f"Cannot delete active profile '{profile_name}'. Set a different active profile first."
            )

        del self._config[profile_name]
        self._save_config()

    def get_config_path(self) -> str:
        """Get the path to the configuration file."""
        return str(self.config_path)

    def _validate_profile_config(self, profile_config: Dict[str, Any]) -> None:
        """Validate a profile configuration."""
        if not isinstance(profile_config, dict):
            raise ConfigurationError("Profile configuration must be a dictionary")

        # Check for required fields
        required_fields = ["platform"]
        for field in required_fields:
            if field not in profile_config:
                raise ConfigurationError(
                    f"Profile configuration missing required field: {field}"
                )

        # Validate platform
        platform = profile_config.get("platform")
        if not isinstance(platform, str) or not platform:
            raise ConfigurationError("Platform must be a non-empty string")

        # Validate platform-specific required fields
        if platform.lower() == "snowflake":
            snowflake_required = ["account", "username", "database", "schema"]
            for field in snowflake_required:
                if field not in profile_config:
                    raise ConfigurationError(
                        f"Snowflake profile missing required field: {field}"
                    )

    def validate_profile(self, profile_name: str) -> List[str]:
        """Validate a specific profile and return list of errors."""
        errors = []

        profile = self.get_profile(profile_name)
        if not profile:
            errors.append(f"Profile '{profile_name}' does not exist")
            return errors

        try:
            self._validate_profile_config(profile)
        except ConfigurationError as e:
            errors.append(str(e))

        return errors

    def get_active_profile_config(self) -> Optional[Dict[str, Any]]:
        """Get the configuration for the currently active profile."""
        active_profile = self.get_active_profile()
        if active_profile:
            return self.get_profile(active_profile)
        return None

    def profile_exists(self, profile_name: str) -> bool:
        """Check if a profile exists."""
        return profile_name in self._config

    def get_profile_count(self) -> int:
        """Get the total number of profiles."""
        return len(self.list_profiles())
 