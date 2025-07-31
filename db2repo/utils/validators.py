"""
Validation utilities for DB2Repo.

This module contains functions for validating configuration and inputs.
"""

from typing import Any, Dict


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure."""
    # This will be implemented in future stories
    return True


def validate_profile(profile_config: Dict[str, Any]) -> bool:
    """Validate profile configuration."""
    # This will be implemented in future stories
    return True

def to_snowflake_name(branch_name: str) -> str:
    """
    Convert a Git branch name to a Snowflake-compliant object name.
    
    Snowflake naming rules:
    - Must start with a letter or underscore
    - Can contain letters, digits, and underscores
    - Cannot contain hyphens, spaces, or special characters
    - Maximum 255 characters
    
    Args:
        branch_name: The Git branch name to convert
        
    Returns:
        A Snowflake-compliant name
    """
    if not branch_name:
        return "BRANCH"
    
    # Replace hyphens and other invalid characters with underscores
    import re
    snowflake_name = re.sub(r'[^a-zA-Z0-9_]', '_', branch_name)
    
    # Ensure it starts with a letter or underscore
    if snowflake_name and not snowflake_name[0].isalpha() and snowflake_name[0] != '_':
        snowflake_name = f"branch_{snowflake_name}"
    
    # Remove consecutive underscores
    snowflake_name = re.sub(r'_+', '_', snowflake_name)
    
    # Remove leading/trailing underscores
    snowflake_name = snowflake_name.strip('_')
    
    # Ensure it's not empty
    if not snowflake_name:
        snowflake_name = "branch"
    
    # Truncate if too long (Snowflake limit is 255, but let's be conservative)
    if len(snowflake_name) > 50:
        snowflake_name = snowflake_name[:50]
    
    # Convert to uppercase for Snowflake
    return snowflake_name.upper()
