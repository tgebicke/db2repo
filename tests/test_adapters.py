"""
Tests for AdapterFactory and adapter registration system.
"""

import pytest
from db2repo.adapters import AdapterFactory, DatabaseAdapter
from db2repo.adapters.snowflake import SnowflakeAdapter
from unittest.mock import patch, MagicMock
from db2repo.exceptions import DatabaseConnectionError


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


def make_snowflake_config(auth_method="username_password"):
    cfg = {
        "platform": "snowflake",
        "account": "acct",
        "username": "user",
        "database": "db",
        "schema": "public",
        "auth_method": auth_method,
    }
    if auth_method == "username_password":
        cfg["password"] = "pw"
    elif auth_method == "ssh_key":
        cfg["private_key_path"] = "dummy_path"
    return cfg


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_username_password(mock_snowflake):
    mock_conn = MagicMock()
    mock_snowflake.connector.connect.return_value = mock_conn
    adapter = SnowflakeAdapter(make_snowflake_config())
    assert adapter.connect() is True
    assert adapter._connection == mock_conn


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_external_browser(mock_snowflake):
    mock_conn = MagicMock()
    mock_snowflake.connector.connect.return_value = mock_conn
    cfg = make_snowflake_config("external_browser")
    adapter = SnowflakeAdapter(cfg)
    assert adapter.connect() is True
    assert adapter._connection == mock_conn
    args = mock_snowflake.connector.connect.call_args[1]
    assert args["authenticator"] == "externalbrowser"


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_ssh_key_reads_file(mock_snowflake, tmp_path):
    key_path = tmp_path / "key.pem"
    key_path.write_bytes(b"PRIVATEKEY")
    mock_conn = MagicMock()
    mock_snowflake.connector.connect.return_value = mock_conn
    cfg = make_snowflake_config("ssh_key")
    cfg["private_key_path"] = str(key_path)
    adapter = SnowflakeAdapter(cfg)
    assert adapter.connect() is True
    assert adapter._connection == mock_conn
    args = mock_snowflake.connector.connect.call_args[1]
    assert args["private_key"] == b"PRIVATEKEY"


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_raises_on_missing_private_key(mock_snowflake):
    cfg = make_snowflake_config("ssh_key")
    adapter = SnowflakeAdapter(cfg)
    with patch("builtins.open", side_effect=FileNotFoundError("no file")):
        with pytest.raises(DatabaseConnectionError, match="Failed to read private key"):
            adapter.connect()


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_raises_on_unsupported_auth(mock_snowflake):
    cfg = make_snowflake_config("invalid_auth")
    adapter = SnowflakeAdapter(cfg)
    with pytest.raises(DatabaseConnectionError, match="Unsupported auth_method"):
        adapter.connect()


@patch("db2repo.adapters.snowflake.snowflake")
def test_connect_raises_on_connect_error(mock_snowflake):
    mock_snowflake.connector.connect.side_effect = Exception("fail connect")
    adapter = SnowflakeAdapter(make_snowflake_config())
    with pytest.raises(DatabaseConnectionError, match="Failed to connect to Snowflake"):
        adapter.connect()


@patch("db2repo.adapters.snowflake.snowflake")
def test_disconnect_closes_connection(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    adapter._connection = mock_conn
    adapter.disconnect()
    mock_conn.close.assert_called_once()
    assert adapter._connection is None


@patch("db2repo.adapters.snowflake.snowflake")
def test_test_connection_success(mock_snowflake):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.return_value = (1,)
    adapter = SnowflakeAdapter(make_snowflake_config())
    adapter._connection = mock_conn
    assert adapter.test_connection() is True
    mock_cursor.execute.assert_called_once_with("SELECT 1")
    mock_cursor.close.assert_called_once()


@patch("db2repo.adapters.snowflake.snowflake")
def test_test_connection_failure(mock_snowflake):
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("fail cursor")
    adapter = SnowflakeAdapter(make_snowflake_config())
    adapter._connection = mock_conn
    with pytest.raises(DatabaseConnectionError, match="Connection test failed"):
        adapter.test_connection()
