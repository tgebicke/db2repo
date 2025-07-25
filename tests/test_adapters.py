"""
Tests for AdapterFactory and adapter registration system.
"""

import pytest
from db2repo.adapters import AdapterFactory, DatabaseAdapter
from db2repo.adapters.snowflake import SnowflakeAdapter


class DummyAdapter(DatabaseAdapter):
    def connect(self):
        return True

    def disconnect(self):
        pass

    def get_tables(self, database, schema):
        return []

    def get_views(self, database, schema):
        return []

    def get_materialized_views(self, database, schema):
        return []

    def get_stages(self, database, schema):
        return []

    def get_snowpipes(self, database, schema):
        return []

    def get_stored_procedures(self, database, schema):
        return []

    def test_connection(self):
        return True


def test_factory_returns_snowflake_adapter():
    config = {
        "platform": "snowflake",
        "account": "a",
        "username": "u",
        "database": "d",
        "schema": "s",
    }
    adapter = AdapterFactory.get_adapter(config)
    assert isinstance(adapter, SnowflakeAdapter)
    assert adapter.config == config


def test_factory_register_and_get_dummy_adapter():
    AdapterFactory.register_adapter("dummy", DummyAdapter)
    config = {"platform": "dummy"}
    adapter = AdapterFactory.get_adapter(config)
    assert isinstance(adapter, DummyAdapter)
    assert adapter.config == config


def test_factory_raises_for_unknown_platform():
    config = {"platform": "unknown"}
    with pytest.raises(
        ValueError, match="No adapter registered for platform 'unknown'"
    ):
        AdapterFactory.get_adapter(config)


def test_factory_raises_for_missing_platform():
    config = {}
    with pytest.raises(ValueError, match="No platform specified in config"):
        AdapterFactory.get_adapter(config)
