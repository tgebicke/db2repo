import tempfile
from pathlib import Path
import pytest
from db2repo.utils.file_organization import (
    normalize_name,
    get_ddl_file_path,
    write_ddl_file,
    validate_ddl_file_structure,
)

def test_normalize_name():
    assert normalize_name("My Table") == "my_table"
    assert normalize_name("My-Table@2024!") == "my_table_2024_"
    assert normalize_name("SOME$SCHEMA") == "some_schema"
    assert normalize_name("a b c") == "a_b_c"

def test_get_ddl_file_path():
    path = get_ddl_file_path("/base", "DB", "SCHEMA", "Table", "My Table")
    assert str(path).endswith("/base/db/schema/table/my_table.sql")
    path = get_ddl_file_path("/base", "DB", "SCHEMA", "View", "Obj", ".ddl")
    assert str(path).endswith("/base/db/schema/view/obj.ddl")

def test_write_and_validate_ddl_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = write_ddl_file(tmpdir, "DB", "SCHEMA", "Table", "My Table", "CREATE TABLE ...;")
        assert file_path.exists()
        assert file_path.read_text().strip() == "CREATE TABLE ...;"
        assert validate_ddl_file_structure(tmpdir, "DB", "SCHEMA", "Table", "My Table")

def test_write_ddl_file_overwrite_and_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = write_ddl_file(tmpdir, "DB", "SCHEMA", "Table", "Obj", "DDL1")
        # Overwrite allowed
        file_path2 = write_ddl_file(tmpdir, "DB", "SCHEMA", "Table", "Obj", "DDL2", overwrite=True)
        assert file_path2.read_text().strip() == "DDL2"
        # Overwrite not allowed
        with pytest.raises(FileExistsError):
            write_ddl_file(tmpdir, "DB", "SCHEMA", "Table", "Obj", "DDL3", overwrite=False)

def test_special_characters_in_names():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = write_ddl_file(tmpdir, "D B$", "S@C", "Ta-ble", "Obj!@#", "DDL")
        assert "d_b_" in str(file_path)
        assert "s_c" in str(file_path)
        assert "ta_ble" in str(file_path)
        assert "obj_" in str(file_path)
        assert file_path.exists() 