"""
Configuration management module for DB2Repo.

This module handles loading, saving, and managing configuration files
in TOML format with profile-based settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import toml


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
            except toml.TomlDecodeError as e:
                raise ValueError(f"Invalid TOML configuration file: {e}")
        else:
            self._config = {}

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
        self._config[profile_name] = profile_config
        self._save_config()

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        profiles = []
        for key in self._config.keys():
            if key != "active_profile":
                profiles.append(key)
        return profiles

    def delete_profile(self, profile_name: str) -> None:
        """Delete a profile."""
        if profile_name in self._config:
            del self._config[profile_name]
            self._save_config()

    def get_config_path(self) -> str:
        """Get the path to the configuration file."""
        return str(self.config_path)
