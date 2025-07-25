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


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_tables_and_error_handling(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    # Simulate two tables, one with DDL, one with error
    mock_cursor.description = [("NAME",), ("CREATED_ON",)]
    mock_cursor.fetchall.return_value = [("T1", "2023-01-01"), ("T2", "2023-01-01")]
    # First table returns DDL, second raises error
    def execute_side_effect(sql):
        if sql.startswith("SELECT GET_DDL") and "T2" in sql:
            raise Exception("DDL error")
        # Do not change description here

    mock_cursor.execute.side_effect = execute_side_effect
    mock_cursor.fetchone.side_effect = [("CREATE TABLE T1 ...",)]
    results = adapter.get_tables("DB", "SCHEMA")
    assert len(results) == 2
    assert results[0]["name"] == "T1"
    assert results[0]["ddl"] == "CREATE TABLE T1 ..."
    assert results[1]["name"] == "T2"
    assert results[1]["ddl"] is None
    assert "error" in results[1]


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_views_and_materialized_views(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [("name",), ("created_on",)]
    mock_cursor.fetchall.return_value = [("V1", "2023-01-01")]
    mock_cursor.execute.side_effect = None
    mock_cursor.fetchone.side_effect = [("2023-01-01", "V1", "CREATE VIEW V1 ...")]
    # Test get_views
    results = adapter.get_views("DB", "SCHEMA")
    assert len(results) == 1
    assert results[0]["type"] == "VIEW"
    # Test get_materialized_views
    results = adapter.get_materialized_views("DB", "SCHEMA")
    assert len(results) == 1
    assert results[0]["type"] == "MATERIALIZED VIEW"


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_stages_and_pipes(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [("name",), ("created_on",)]
    mock_cursor.fetchall.return_value = [("S1", "2023-01-01")]
    mock_cursor.execute.side_effect = None
    mock_cursor.fetchone.side_effect = [("2023-01-01", "S1", "CREATE STAGE S1 ...")]
    # Test get_stages
    results = adapter.get_stages("DB", "SCHEMA")
    assert len(results) == 1
    assert results[0]["type"] == "STAGE"
    # Test get_snowpipes
    results = adapter.get_snowpipes("DB", "SCHEMA")
    assert len(results) == 1
    assert results[0]["type"] == "PIPE"


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_object_ddls_handles_query_error(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("query error")
    with pytest.raises(
        DatabaseConnectionError, match="Failed to fetch TABLEs: query error"
    ):
        adapter.get_tables("DB", "SCHEMA")


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_stored_procedures_sql(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [
        ("PROCEDURE_NAME",),
        ("ARGUMENT_SIGNATURE",),
        ("PROCEDURE_LANGUAGE",),
        ("PROCEDURE_DEFINITION",),
        ("DATA_TYPE",),
    ]
    mock_cursor.fetchall.return_value = [
        ("MYPROC", "(a INT)", "SQL", "BEGIN RETURN a+1; END;", "INT")
    ]
    results = adapter.get_stored_procedures("DB", "SCHEMA")
    assert len(results) == 1
    ddl = results[0]["ddl"]
    assert "CREATE OR REPLACE PROCEDURE DB.SCHEMA.MYPROC (a INT)" in ddl
    assert "RETURNS INT" in ddl
    assert "LANGUAGE SQL" in ddl
    assert "BEGIN RETURN a+1; END;" in ddl
    assert "$$" not in ddl


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_stored_procedures_js_and_python(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [
        ("PROCEDURE_NAME",),
        ("ARGUMENT_SIGNATURE",),
        ("PROCEDURE_LANGUAGE",),
        ("PROCEDURE_DEFINITION",),
        ("DATA_TYPE",),
    ]
    mock_cursor.fetchall.return_value = [
        ("MYJS", "(x INT)", "JAVASCRIPT", "return x+1;", "INT"),
        ("MYPY", "(y INT)", "PYTHON", "return y+1", "INT"),
    ]
    results = adapter.get_stored_procedures("DB", "SCHEMA")
    assert len(results) == 2
    assert results[0]["language"].upper() == "JAVASCRIPT"
    assert "$$" in results[0]["ddl"]
    assert results[1]["language"].upper() == "PYTHON"
    assert "$$" in results[1]["ddl"]


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_stored_procedures_error_handling(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [
        ("PROCEDURE_NAME",),
        ("ARGUMENT_SIGNATURE",),
        ("PROCEDURE_LANGUAGE",),
        ("PROCEDURE_DEFINITION",),
        ("DATA_TYPE",),
    ]
    # Malformed tuple (missing DATA_TYPE)
    mock_cursor.fetchall.return_value = [
        ("BADPROC", "(z INT)", "SQL", "BEGIN RETURN z; END;")
    ]
    results = adapter.get_stored_procedures("DB", "SCHEMA")
    assert len(results) == 1
    assert results[0]["ddl"] is None
    assert "error" in results[0]


@patch("db2repo.adapters.snowflake.snowflake")
def test_get_stored_procedures_query_error(mock_snowflake):
    adapter = SnowflakeAdapter(make_snowflake_config())
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    adapter._connection = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = Exception("query error")
    with pytest.raises(
        DatabaseConnectionError, match="Failed to fetch procedures: query error"
    ):
        adapter.get_stored_procedures("DB", "SCHEMA")
