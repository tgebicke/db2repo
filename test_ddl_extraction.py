#!/usr/bin/env python3
"""Test DDL extraction with mock data."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db2repo.utils.file_organization import write_ddl_file
from pathlib import Path
import tempfile

def test_ddl_extraction():
    """Test DDL extraction with mock data."""
    
    # Mock DDL data
    mock_objects = [
        {
            "name": "CUSTOMERS",
            "type": "TABLE",
            "database": "DB2REPO_TEST",
            "schema": "TEST_SCHEMA",
            "ddl": """CREATE OR REPLACE TABLE CUSTOMERS (
    CUSTOMER_ID NUMBER AUTOINCREMENT,
    FIRST_NAME VARCHAR(50) NOT NULL,
    LAST_NAME VARCHAR(50) NOT NULL,
    EMAIL VARCHAR(100) UNIQUE,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    IS_ACTIVE BOOLEAN DEFAULT TRUE
);"""
        },
        {
            "name": "ACTIVE_CUSTOMERS",
            "type": "VIEW",
            "database": "DB2REPO_TEST",
            "schema": "TEST_SCHEMA",
            "ddl": """CREATE OR REPLACE VIEW ACTIVE_CUSTOMERS AS
SELECT 
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    CREATED_DATE
FROM CUSTOMERS 
WHERE IS_ACTIVE = TRUE;"""
        },
        {
            "name": "GET_CUSTOMER_ORDERS",
            "type": "PROCEDURE",
            "database": "DB2REPO_TEST",
            "schema": "TEST_SCHEMA",
            "ddl": """CREATE OR REPLACE PROCEDURE GET_CUSTOMER_ORDERS(CUSTOMER_ID_PARAM VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
DECLARE
    result VARCHAR DEFAULT '';
    c1 CURSOR FOR 
        SELECT ORDER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS
        FROM ORDERS
        WHERE CUSTOMER_ID = CUSTOMER_ID_PARAM::NUMBER
        ORDER BY ORDER_DATE DESC;
BEGIN
    FOR record IN c1 DO
        result := result || 'Order ID: ' || record.ORDER_ID || 
                  ', Date: ' || record.ORDER_DATE || 
                  ', Amount: ' || record.TOTAL_AMOUNT || 
                  ', Status: ' || record.STATUS || '; ';
    END FOR;
    RETURN result;
END;
$$;"""
        }
    ]
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Testing DDL extraction in: {tmpdir}")
        
        successful_objects = 0
        failed_objects = 0
        
        for obj in mock_objects:
            try:
                file_path = write_ddl_file(
                    base_dir=tmpdir,
                    database=obj["database"],
                    schema=obj["schema"],
                    object_type=obj["type"],
                    object_name=obj["name"],
                    ddl=obj["ddl"],
                    overwrite=True
                )
                
                print(f"✅ Created: {file_path}")
                successful_objects += 1
                
                # Verify file was created and contains DDL
                if file_path.exists():
                    content = file_path.read_text()
                    if obj["ddl"] in content:
                        print(f"   ✅ DDL content verified")
                    else:
                        print(f"   ❌ DDL content mismatch")
                        failed_objects += 1
                else:
                    print(f"   ❌ File not created")
                    failed_objects += 1
                    
            except Exception as e:
                print(f"❌ Error creating {obj['type']} {obj['name']}: {e}")
                failed_objects += 1
        
        print(f"\nTest Summary:")
        print(f"  Successful: {successful_objects}")
        print(f"  Failed: {failed_objects}")
        
        # List all created files
        print(f"\nCreated files:")
        for file_path in Path(tmpdir).rglob("*.sql"):
            print(f"  {file_path.relative_to(tmpdir)}")

if __name__ == "__main__":
    test_ddl_extraction() 