"""
Database adapters package for DB2Repo.

This package contains database-specific adapters that implement
the common interface for DDL extraction.
"""

from .base import DatabaseAdapter

__all__ = ["DatabaseAdapter"]
