"""
Custom exceptions for DB2Repo.

This module defines custom exception classes used throughout the application.
"""


class DB2RepoError(Exception):
    """Base exception for DB2Repo."""

    pass


class ConfigurationError(DB2RepoError):
    """Raised when there's a configuration error."""

    pass


class DatabaseConnectionError(DB2RepoError):
    """Raised when database connection fails."""

    pass


class GitOperationError(DB2RepoError):
    """Raised when git operations fail."""

    pass
