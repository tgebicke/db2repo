"""
DB2Repo - Database DDL to Git Repository Tool

A command-line interface tool for tracking database DDL (Data Definition Language)
in a git repository. Supports multiple database platforms with an extensible
adapter pattern, starting with Snowflake.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@company.com"

from .cli import cli

__all__ = ["cli"]
