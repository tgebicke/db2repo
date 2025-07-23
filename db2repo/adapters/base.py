"""
Abstract base class for database adapters.

This module defines the common interface that all database adapters
must implement for DDL extraction.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the database adapter.

        Args:
            config: Configuration dictionary for the database connection
        """
        self.config = config
        self._connection: Optional[Any] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def get_tables(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """
        Get DDL for all tables in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing table information and DDL
        """
        pass

    @abstractmethod
    def get_views(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """
        Get DDL for all views in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing view information and DDL
        """
        pass

    @abstractmethod
    def get_materialized_views(
        self, database: str, schema: str
    ) -> List[Dict[str, Any]]:
        """
        Get DDL for all materialized views in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing materialized view information and DDL
        """
        pass

    @abstractmethod
    def get_stages(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """
        Get DDL for all stages in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing stage information and DDL
        """
        pass

    @abstractmethod
    def get_snowpipes(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """
        Get DDL for all snow pipes in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing snow pipe information and DDL
        """
        pass

    @abstractmethod
    def get_stored_procedures(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """
        Get DDL for all stored procedures in the specified database and schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of dictionaries containing stored procedure information and DDL
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection test successful, False otherwise
        """
        pass

    def get_platform_name(self) -> str:
        """
        Get the platform name for this adapter.

        Returns:
            Platform name (e.g., 'snowflake', 'postgresql')
        """
        return self.__class__.__name__.lower().replace("adapter", "")
