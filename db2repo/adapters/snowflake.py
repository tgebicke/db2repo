"""
Snowflake database adapter for DB2Repo.

This module implements the DatabaseAdapter interface for Snowflake databases.
"""

from typing import Any, Dict, List

from .base import DatabaseAdapter
from db2repo.exceptions import DatabaseConnectionError

try:
    import snowflake.connector
except ImportError:
    snowflake = None


class SnowflakeAdapter(DatabaseAdapter):
    """Snowflake database adapter implementation."""

    def connect(self) -> bool:
        """Establish connection to Snowflake database."""
        if not snowflake:
            raise DatabaseConnectionError(
                "snowflake-connector-python is not installed."
            )
        
        # Set environment variable to work around CFFI issue
        import os
        os.environ['CFFI_ALLOW_SOURCE_CODE'] = '1'
        
        cfg = self.config
        conn_args = {
            "account": cfg.get("account"),
            "user": cfg.get("username"),
            "database": cfg.get("database"),
            "schema": cfg.get("schema"),
        }
        auth_method = cfg.get("auth_method", "username_password")
        if auth_method == "username_password":
            conn_args["password"] = cfg.get("password")
        elif auth_method == "ssh_key":
            private_key_path = cfg.get("private_key_path")
            if not private_key_path:
                raise DatabaseConnectionError(
                    "Missing private_key_path for SSH key auth."
                )
            try:
                with open(private_key_path, "rb") as key_file:
                    private_key = key_file.read()
                conn_args["private_key"] = private_key
            except Exception as e:
                raise DatabaseConnectionError(f"Failed to read private key: {e}")
        elif auth_method == "external_browser":
            conn_args["authenticator"] = "externalbrowser"
        else:
            raise DatabaseConnectionError(f"Unsupported auth_method: {auth_method}")
        # Optional fields
        if cfg.get("warehouse"):
            conn_args["warehouse"] = cfg["warehouse"]
        if cfg.get("role"):
            conn_args["role"] = cfg["role"]
        
        # Add insecure_mode to work around SSL certificate issues
        conn_args["insecure_mode"] = True
        
        try:
            self._connection = snowflake.connector.connect(**conn_args)
            return True
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to Snowflake: {e}")

    def disconnect(self) -> None:
        """Close the Snowflake database connection."""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None

    def get_tables(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all tables in the specified database and schema."""
        return self._get_object_ddls(database, schema, "TABLE")

    def get_views(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all views in the specified database and schema."""
        return self._get_object_ddls(database, schema, "VIEW")

    def get_materialized_views(
        self, database: str, schema: str
    ) -> List[Dict[str, Any]]:
        """Get DDL for all materialized views in the specified database and schema."""
        # For materialized views, we need to use SHOW MATERIALIZED VIEWS
        return self._get_materialized_view_ddls(database, schema)

    def get_stages(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all stages in the specified database and schema."""
        # For stages, we need to use SHOW CREATE STAGE instead of GET_DDL
        return self._get_stage_ddls(database, schema)

    def get_snowpipes(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all snow pipes in the specified database and schema."""
        return self._get_object_ddls(database, schema, "PIPE")

    def _get_object_ddls(
        self, database: str, schema: str, object_type: str
    ) -> List[Dict[str, Any]]:
        """Generic DDL extraction for a given object type."""
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        results = []
        try:
            # Query for object names
            cursor.execute(f"SHOW {object_type}s IN SCHEMA {database}.{schema}")
            objects = cursor.fetchall()
            name_idx = [desc[0].upper() for desc in cursor.description].index("NAME")
            for obj in objects:
                obj_name = obj[name_idx]
                try:
                    # Use GET_DDL function instead of SHOW CREATE
                    cursor.execute(
                        f"SELECT GET_DDL('{object_type}', '{database}.{schema}.{obj_name}')"
                    )
                    ddl_row = cursor.fetchone()
                    ddl = ddl_row[0] if ddl_row else None
                    results.append(
                        {
                            "name": obj_name,
                            "type": object_type,
                            "database": database,
                            "schema": schema,
                            "ddl": ddl,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "name": obj_name,
                            "type": object_type,
                            "database": database,
                            "schema": schema,
                            "ddl": None,
                            "error": str(e),
                        }
                    )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to fetch {object_type}s: {e}")
        finally:
            cursor.close()
        return results

    def _get_stage_ddls(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all stages using SHOW CREATE STAGE."""
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        results = []
        try:
            # Query for stage names
            cursor.execute(f"SHOW STAGES IN SCHEMA {database}.{schema}")
            stages = cursor.fetchall()
            name_idx = [desc[0].upper() for desc in cursor.description].index("NAME")
            for stage in stages:
                stage_name = stage[name_idx]
                try:
                    # Use DESCRIBE STAGE for stages (SHOW CREATE doesn't work for stages)
                    cursor.execute(f"DESCRIBE STAGE {database}.{schema}.{stage_name}")
                    stage_info = cursor.fetchall()
                    # Build DDL from stage description
                    ddl_lines = [f"CREATE OR REPLACE STAGE {database}.{schema}.{stage_name}"]
                    for row in stage_info:
                        if row[0] == "URL":
                            ddl_lines.append(f"URL = '{row[1]}'")
                        elif row[0] == "STORAGE_INTEGRATION":
                            ddl_lines.append(f"STORAGE_INTEGRATION = {row[1]}")
                        elif row[0] == "CREDENTIALS":
                            ddl_lines.append(f"CREDENTIALS = ({row[1]})")
                    ddl = ";\n".join(ddl_lines) + ";"
                    results.append(
                        {
                            "name": stage_name,
                            "type": "STAGE",
                            "database": database,
                            "schema": schema,
                            "ddl": ddl,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "name": stage_name,
                            "type": "STAGE",
                            "database": database,
                            "schema": schema,
                            "ddl": None,
                            "error": str(e),
                        }
                    )
        except Exception as e:
            # If no stages exist, return empty list
            pass
        cursor.close()
        return results

    def _get_materialized_view_ddls(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all materialized views using SHOW MATERIALIZED VIEWS."""
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        results = []
        try:
            # Query for materialized view names
            cursor.execute(f"SHOW MATERIALIZED VIEWS IN SCHEMA {database}.{schema}")
            views = cursor.fetchall()
            name_idx = [desc[0].upper() for desc in cursor.description].index("NAME")
            for view in views:
                view_name = view[name_idx]
                try:
                    # Use GET_DDL for materialized views
                    cursor.execute(f"SELECT GET_DDL('MATERIALIZED_VIEW', '{database}.{schema}.{view_name}')")
                    ddl_row = cursor.fetchone()
                    ddl = ddl_row[0] if ddl_row else None
                    results.append(
                        {
                            "name": view_name,
                            "type": "MATERIALIZED_VIEW",
                            "database": database,
                            "schema": schema,
                            "ddl": ddl,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "name": view_name,
                            "type": "MATERIALIZED_VIEW",
                            "database": database,
                            "schema": schema,
                            "ddl": None,
                            "error": str(e),
                        }
                    )
        except Exception as e:
            # If no materialized views exist, return empty list
            pass
        cursor.close()
        return results

    def get_stored_procedures(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """Get DDL for all stored procedures in the specified database and schema."""
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        results = []
        try:
            # Get all procedures from information_schema
            cursor.execute(
                f"SELECT PROCEDURE_NAME, ARGUMENT_SIGNATURE, PROCEDURE_LANGUAGE, PROCEDURE_DEFINITION, DATA_TYPE FROM {database}.INFORMATION_SCHEMA.PROCEDURES WHERE PROCEDURE_SCHEMA = %s",
                (schema,),
            )
            procs = cursor.fetchall()
            desc = [d[0].upper() for d in cursor.description]
            idx_name = desc.index("PROCEDURE_NAME")
            idx_args = desc.index("ARGUMENT_SIGNATURE")
            idx_lang = desc.index("PROCEDURE_LANGUAGE")
            idx_body = desc.index("PROCEDURE_DEFINITION")
            idx_ret = desc.index("DATA_TYPE")
            for proc in procs:
                try:
                    name = proc[idx_name]
                    args = proc[idx_args]
                    lang = proc[idx_lang]
                    body = proc[idx_body]
                    ret = proc[idx_ret]
                    # Reconstruct header
                    header = f"CREATE OR REPLACE PROCEDURE {database}.{schema}.{name} {args}\nRETURNS {ret}\nLANGUAGE {lang}\nAS"
                    # For SQL, body is not quoted; for JS/Python, may need $$
                    if lang.upper() == "SQL":
                        ddl = f"{header}\n{body.strip()}"
                    else:
                        # Use $$ for JS/Python
                        ddl = f"{header}\n$$\n{body.strip()}\n$$"
                    results.append(
                        {
                            "name": name,
                            "type": "PROCEDURE",
                            "database": database,
                            "schema": schema,
                            "language": lang,
                            "ddl": ddl,
                        }
                    )
                except Exception as e:
                    # Handle malformed or missing fields per-procedure
                    name = proc[idx_name] if len(proc) > idx_name else None
                    lang = proc[idx_lang] if len(proc) > idx_lang else None
                    results.append(
                        {
                            "name": name,
                            "type": "PROCEDURE",
                            "database": database,
                            "schema": schema,
                            "language": lang,
                            "ddl": None,
                            "error": str(e),
                        }
                    )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to fetch procedures: {e}")
        finally:
            cursor.close()
        return results

    def test_connection(self) -> bool:
        """Test the Snowflake database connection."""
        try:
            if not self._connection:
                self.connect()
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            raise DatabaseConnectionError(f"Connection test failed: {e}")
