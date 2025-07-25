import os
import re
from pathlib import Path
from typing import Optional

def normalize_name(name: str) -> str:
    """Normalize object names for filesystem (lowercase, replace spaces/special chars)."""
    # Replace spaces and special chars with underscores, lowercase
    return re.sub(r"[^a-zA-Z0-9_]+", "_", name).lower()

def get_ddl_file_path(
    base_dir: str,
    database: str,
    schema: str,
    object_type: str,
    object_name: str,
    extension: str = ".sql",
) -> Path:
    """Construct the file path for a DDL object."""
    db = normalize_name(database)
    sch = normalize_name(schema)
    obj_type = normalize_name(object_type)
    obj_name = normalize_name(object_name)
    return Path(base_dir) / db / sch / obj_type / f"{obj_name}{extension}"

def write_ddl_file(
    base_dir: str,
    database: str,
    schema: str,
    object_type: str,
    object_name: str,
    ddl: str,
    extension: str = ".sql",
    overwrite: bool = True,
) -> Path:
    """Write DDL to the appropriate file, creating directories as needed."""
    file_path = get_ddl_file_path(base_dir, database, schema, object_type, object_name, extension)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(ddl.strip() + "\n")
    return file_path

def validate_ddl_file_structure(base_dir: str, database: str, schema: str, object_type: str, object_name: str) -> bool:
    """Validate that the DDL file exists in the expected location."""
    file_path = get_ddl_file_path(base_dir, database, schema, object_type, object_name)
    return file_path.exists() 