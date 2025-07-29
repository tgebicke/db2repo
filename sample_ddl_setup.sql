-- Sample DDL Setup for DB2Repo Testing
-- Run this in your Snowflake account to create test objects

-- Create test database and schema
CREATE DATABASE IF NOT EXISTS DB2REPO_TEST;
USE DATABASE DB2REPO_TEST;
CREATE SCHEMA IF NOT EXISTS TEST_SCHEMA;
USE SCHEMA TEST_SCHEMA;

-- 1. TABLES
-- Simple table
CREATE OR REPLACE TABLE CUSTOMERS (
    CUSTOMER_ID NUMBER AUTOINCREMENT,
    FIRST_NAME VARCHAR(50) NOT NULL,
    LAST_NAME VARCHAR(50) NOT NULL,
    EMAIL VARCHAR(100) UNIQUE,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    IS_ACTIVE BOOLEAN DEFAULT TRUE
);

-- Table with customer reference
CREATE OR REPLACE TABLE ORDERS (
    ORDER_ID NUMBER AUTOINCREMENT,
    CUSTOMER_ID NUMBER NOT NULL,
    ORDER_DATE DATE NOT NULL,
    TOTAL_AMOUNT DECIMAL(10,2) NOT NULL,
    STATUS VARCHAR(20) DEFAULT 'PENDING'
);

-- Table with clustering
CREATE OR REPLACE TABLE ORDER_ITEMS (
    ITEM_ID NUMBER AUTOINCREMENT,
    ORDER_ID NUMBER NOT NULL,
    PRODUCT_NAME VARCHAR(100) NOT NULL,
    QUANTITY NUMBER NOT NULL,
    UNIT_PRICE DECIMAL(10,2) NOT NULL,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) CLUSTER BY (ORDER_ID, CREATED_AT);

-- 2. VIEWS
-- Simple view
CREATE OR REPLACE VIEW ACTIVE_CUSTOMERS AS
SELECT 
    CUSTOMER_ID,
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    CREATED_DATE
FROM CUSTOMERS 
WHERE IS_ACTIVE = TRUE;

-- Complex view with joins
CREATE OR REPLACE VIEW CUSTOMER_ORDER_SUMMARY AS
SELECT 
    c.CUSTOMER_ID,
    c.FIRST_NAME,
    c.LAST_NAME,
    COUNT(o.ORDER_ID) as TOTAL_ORDERS,
    SUM(o.TOTAL_AMOUNT) as TOTAL_SPENT,
    MAX(o.ORDER_DATE) as LAST_ORDER_DATE
FROM CUSTOMERS c
LEFT JOIN ORDERS o ON c.CUSTOMER_ID = o.CUSTOMER_ID
WHERE c.IS_ACTIVE = TRUE
GROUP BY c.CUSTOMER_ID, c.FIRST_NAME, c.LAST_NAME;

-- 3. MATERIALIZED VIEWS
-- Materialized view (Snowflake calls these "Materialized Views")
CREATE OR REPLACE MATERIALIZED VIEW DAILY_SALES_SUMMARY AS
SELECT 
    DATE(ORDER_DATE) as SALE_DATE,
    COUNT(*) as TOTAL_ORDERS,
    SUM(TOTAL_AMOUNT) as DAILY_REVENUE,
    AVG(TOTAL_AMOUNT) as AVG_ORDER_VALUE
FROM ORDERS
WHERE STATUS != 'CANCELLED'
GROUP BY DATE(ORDER_DATE);

-- 4. STAGES
-- Internal stage
CREATE OR REPLACE STAGE INTERNAL_DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1);

-- External stage (S3 example - you'll need to update with your own S3 details)
-- CREATE OR REPLACE STAGE EXTERNAL_S3_STAGE
--     URL = 's3://your-bucket/path/'
--     CREDENTIALS = (AWS_KEY_ID = 'your-key' AWS_SECRET_KEY = 'your-secret')
--     FILE_FORMAT = (TYPE = 'JSON');

-- 5. SNOW PIPES
-- Pipe for loading data from stage
CREATE OR REPLACE PIPE CUSTOMER_DATA_PIPE
    AUTO_INGEST = TRUE
    AS
    COPY INTO CUSTOMERS (FIRST_NAME, LAST_NAME, EMAIL, IS_ACTIVE)
    FROM @INTERNAL_DATA_STAGE
    FILE_FORMAT = (TYPE = 'CSV' FIELD_DELIMITER = ',' SKIP_HEADER = 1)
    ON_ERROR = 'CONTINUE';

-- 6. STORED PROCEDURES
-- SQL stored procedure
CREATE OR REPLACE PROCEDURE GET_CUSTOMER_ORDERS(CUSTOMER_ID_PARAM VARCHAR)
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
$$;

-- JavaScript stored procedure
CREATE OR REPLACE PROCEDURE CALCULATE_CUSTOMER_STATS(CUSTOMER_ID_PARAM VARCHAR)
RETURNS OBJECT
LANGUAGE JAVASCRIPT
AS
$$
function calculateStats(customerId) {
    // Query to get customer data
    var customerQuery = `SELECT FIRST_NAME, LAST_NAME FROM CUSTOMERS WHERE CUSTOMER_ID = ${customerId}`;
    var customerResult = snowflake.execute({sqlText: customerQuery});
    
    if (customerResult.next()) {
        var firstName = customerResult.getColumnValue(1);
        var lastName = customerResult.getColumnValue(2);
        
        // Query to get order statistics
        var statsQuery = `
            SELECT 
                COUNT(*) as TOTAL_ORDERS,
                SUM(TOTAL_AMOUNT) as TOTAL_SPENT,
                AVG(TOTAL_AMOUNT) as AVG_ORDER_VALUE
            FROM ORDERS 
            WHERE CUSTOMER_ID = ${customerId}
        `;
        var statsResult = snowflake.execute({sqlText: statsQuery});
        
        if (statsResult.next()) {
            return {
                customer_name: firstName + " " + lastName,
                total_orders: statsResult.getColumnValue(1),
                total_spent: statsResult.getColumnValue(2),
                avg_order_value: statsResult.getColumnValue(3)
            };
        }
    }
    
    return {error: "Customer not found"};
}

return calculateStats(CUSTOMER_ID_PARAM);
$$;

-- Python stored procedure
CREATE OR REPLACE PROCEDURE ANALYZE_CUSTOMER_BEHAVIOR(CUSTOMER_ID_PARAM VARCHAR)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
HANDLER = 'analyze_customer'
AS
$$
import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, when, count, sum, avg

def analyze_customer(snowpark_session, customer_id):
    # Convert string to number for comparison
    customer_id_num = int(customer_id)
    
    # Get customer data
    customer_df = snowpark_session.table("CUSTOMERS").filter(col("CUSTOMER_ID") == customer_id_num)
    
    if customer_df.count() == 0:
        return "Customer not found"
    
    # Get order data
    orders_df = snowpark_session.table("ORDERS").filter(col("CUSTOMER_ID") == customer_id_num)
    
    # Calculate statistics
    total_orders = orders_df.count()
    total_spent = orders_df.select(sum("TOTAL_AMOUNT")).collect()[0][0] or 0
    avg_order = orders_df.select(avg("TOTAL_AMOUNT")).collect()[0][0] or 0
    
    # Determine customer segment
    if total_spent > 1000:
        segment = "Premium"
    elif total_spent > 500:
        segment = "Regular"
    else:
        segment = "Basic"
    
    return f"Customer Analysis: {total_orders} orders, ${total_spent:.2f} total spent, {segment} segment"
$$;

-- Insert some sample data
INSERT INTO CUSTOMERS (FIRST_NAME, LAST_NAME, EMAIL, IS_ACTIVE) VALUES
('John', 'Doe', 'john.doe@example.com', TRUE),
('Jane', 'Smith', 'jane.smith@example.com', TRUE),
('Bob', 'Johnson', 'bob.johnson@example.com', FALSE),
('Alice', 'Brown', 'alice.brown@example.com', TRUE);

INSERT INTO ORDERS (CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS) VALUES
(1, '2024-01-15', 150.00, 'DELIVERED'),
(1, '2024-02-20', 75.50, 'SHIPPED'),
(2, '2024-01-10', 200.00, 'DELIVERED'),
(2, '2024-03-05', 125.25, 'PROCESSING'),
(4, '2024-02-28', 300.00, 'DELIVERED');

INSERT INTO ORDER_ITEMS (ORDER_ID, PRODUCT_NAME, QUANTITY, UNIT_PRICE) VALUES
(1, 'Laptop', 1, 150.00),
(2, 'Mouse', 2, 25.00),
(2, 'Keyboard', 1, 25.50),
(3, 'Monitor', 1, 200.00),
(4, 'Headphones', 1, 125.25),
(5, 'Tablet', 1, 300.00);

-- Grant necessary permissions (adjust as needed)
GRANT USAGE ON DATABASE DB2REPO_TEST TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC;
GRANT USAGE ON ALL STAGES IN SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC;
GRANT USAGE ON ALL PIPES IN SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC;
GRANT USAGE ON ALL PROCEDURES IN SCHEMA DB2REPO_TEST.TEST_SCHEMA TO ROLE PUBLIC; 