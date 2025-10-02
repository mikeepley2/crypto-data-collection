import os
import sys
sys.path.append('/app')
from shared.database_pool import execute_query

def check_price_data_schema():
    """Check the current schema of price_data_real table"""
    try:
        # Query to describe the table structure
        query = "DESCRIBE price_data_real"
        result = execute_query(query, fetch_results=True)
        
        print("Current price_data_real schema:")
        print("=" * 50)
        for row in result:
            print(f"Field: {row[0]}, Type: {row[1]}, Null: {row[2]}, Key: {row[3]}, Default: {row[4]}, Extra: {row[5]}")
            
        # Check specifically for price_change_24h column
        change_col_query = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'price_data_real' AND COLUMN_NAME = 'price_change_24h'"
        change_result = execute_query(change_col_query, fetch_results=True)
        
        print("\nSpecific info for price_change_24h column:")
        print("=" * 50)
        for row in change_result:
            print(f"Column: {row[0]}, Type: {row[1]}, Max Length: {row[2]}, Precision: {row[3]}, Scale: {row[4]}")
            
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_price_data_schema()