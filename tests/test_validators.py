"""
Tests for the validators module.
"""

import pytest
from db2repo.utils.validators import validate_config, validate_profile, to_snowflake_name


class TestValidators:
    """Test cases for validator functions."""

    def test_validate_config(self):
        """Test validate_config function."""
        config = {"active_profile": "test"}
        assert validate_config(config) is True

    def test_validate_profile(self):
        """Test validate_profile function."""
        profile = {"platform": "snowflake"}
        assert validate_profile(profile) is True

    def test_to_snowflake_name_basic(self):
        """Test basic branch name conversion."""
        assert to_snowflake_name("test-feature") == "TEST_FEATURE"
        assert to_snowflake_name("feature/add-new-table") == "FEATURE_ADD_NEW_TABLE"
        assert to_snowflake_name("123-fix-bug") == "BRANCH_123_FIX_BUG"

    def test_to_snowflake_name_special_chars(self):
        """Test branch names with special characters."""
        assert to_snowflake_name("feature@#$%") == "FEATURE"
        assert to_snowflake_name("test!@#$%^&*()") == "TEST"
        assert to_snowflake_name("branch-with.dots") == "BRANCH_WITH_DOTS"

    def test_to_snowflake_name_numbers(self):
        """Test branch names starting with numbers."""
        assert to_snowflake_name("123-branch") == "BRANCH_123_BRANCH"
        assert to_snowflake_name("456") == "BRANCH_456"
        assert to_snowflake_name("789-test") == "BRANCH_789_TEST"

    def test_to_snowflake_name_underscores(self):
        """Test branch names with underscores."""
        assert to_snowflake_name("test_feature") == "TEST_FEATURE"
        assert to_snowflake_name("feature__test") == "FEATURE_TEST"
        assert to_snowflake_name("_test_") == "TEST"

    def test_to_snowflake_name_empty(self):
        """Test empty and None branch names."""
        assert to_snowflake_name("") == "BRANCH"
        assert to_snowflake_name(None) == "BRANCH"

    def test_to_snowflake_name_length(self):
        """Test branch names that are too long."""
        long_branch = "a" * 100
        result = to_snowflake_name(long_branch)
        assert len(result) <= 50
        assert result == "A" * 50

    def test_to_snowflake_name_case_sensitivity(self):
        """Test that output is always uppercase."""
        assert to_snowflake_name("Test-Feature") == "TEST_FEATURE"
        assert to_snowflake_name("TEST-FEATURE") == "TEST_FEATURE"
        assert to_snowflake_name("test-feature") == "TEST_FEATURE" 