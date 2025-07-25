"""
Database adapters package for DB2Repo.

This package contains database-specific adapters that implement
the common interface for DDL extraction.
"""

from .base import DatabaseAdapter
from .snowflake import SnowflakeAdapter
from typing import Dict, Type, Any


class AdapterFactory:
    """Factory for creating database adapters based on platform name."""

    _registry: Dict[str, Type[DatabaseAdapter]] = {}

    @classmethod
    def register_adapter(
        cls, platform: str, adapter_cls: Type[DatabaseAdapter]
    ) -> None:
        cls._registry[platform.lower()] = adapter_cls

    @classmethod
    def get_adapter(cls, config: Dict[str, Any]) -> DatabaseAdapter:
        platform = config.get("platform", "").lower()
        if not platform:
            raise ValueError("No platform specified in config.")
        adapter_cls = cls._registry.get(platform)
        if not adapter_cls:
            raise ValueError(f"No adapter registered for platform '{platform}'")
        return adapter_cls(config)


# Register built-in adapters
AdapterFactory.register_adapter("snowflake", SnowflakeAdapter)

__all__ = ["DatabaseAdapter", "AdapterFactory"]
