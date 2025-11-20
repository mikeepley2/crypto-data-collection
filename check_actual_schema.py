#!/usr/bin/env python3
"""
Check Actual Database Schema
Connects to the local database and retrieves the actual table structures
to verify our schema files match reality.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from shared.database_config import get_db_connection
import mysql.connector
import json

def get_table_schema(cursor, table_name):
    """Get detailed schema information for a table"""
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        cursor.execute(f"SHOW CREATE TABLE {table_name}")
        create_table_sql = cursor.fetchone()[1]
        
        cursor.execute(f"SHOW INDEX FROM {table_name}")
        indexes = cursor.fetchall()
        
        return {
            'columns': columns,
            'create_sql': create_table_sql,
            'indexes': indexes
        }
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
        return None

def check_actual_database_schema():
    """Check the actual database schema and compare with our files"""
    print("🔍 Checking actual database schema...")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📊 Found {len(tables)} tables in database: {tables}")
        
        schema_info = {}
        
        for table_name in tables:
            print(f"\n🔧 Analyzing table: {table_name}")
            schema = get_table_schema(cursor, table_name)
            
            if schema:
                schema_info[table_name] = schema
                
                print(f"   Columns: {len(schema['columns'])}")
                for col in schema['columns']:
                    field, type_, null, key, default, extra = col
                    print(f"     {field}: {type_} {'NULL' if null == 'YES' else 'NOT NULL'} {extra}")
                
                print(f"   Indexes: {len(schema['indexes'])}")
                for idx in schema['indexes']:
                    table, non_unique, key_name, seq_in_index, column_name = idx[:5]
                    print(f"     {key_name}: {column_name}")
        
        # Save schema information to file
        schema_file = PROJECT_ROOT / "actual_database_schema.json"
        with open(schema_file, 'w') as f:
            # Convert tuple objects to lists for JSON serialization
            serializable_schema = {}
            for table, info in schema_info.items():
                serializable_schema[table] = {
                    'columns': [list(col) for col in info['columns']],
                    'create_sql': info['create_sql'],
                    'indexes': [list(idx) for idx in info['indexes']]
                }
            json.dump(serializable_schema, f, indent=2, default=str)
        
        print(f"\n📄 Schema information saved to: {schema_file}")
        
        # Check table counts
        print(f"\n📈 Table record counts:")
        for table_name in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} records")
            except Exception as e:
                print(f"   {table_name}: Error counting - {e}")
        
        cursor.close()
        connection.close()
        
        return schema_info
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return None

def compare_with_create_missing_tables():
    """Compare actual schema with create_missing_tables.py"""
    print("\n🔍 Comparing with create_missing_tables.py...")
    
    try:
        # Read create_missing_tables.py
        create_file = PROJECT_ROOT / "create_missing_tables.py"
        if create_file.exists():
            with open(create_file, 'r') as f:
                content = f.read()
                print(f"✅ Found create_missing_tables.py ({len(content)} characters)")
                
                # Look for CREATE TABLE statements
                import re
                table_patterns = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content)
                print(f"📋 Tables defined in create_missing_tables.py: {table_patterns}")
        else:
            print("⚠️  create_missing_tables.py not found")
            
    except Exception as e:
        print(f"❌ Error reading create_missing_tables.py: {e}")

def main():
    """Main function"""
    print("🚀 Database Schema Verification")
    print("=" * 50)
    
    # Check actual database
    schema_info = check_actual_database_schema()
    
    if schema_info:
        # Compare with create_missing_tables.py
        compare_with_create_missing_tables()
        
        print(f"\n🎉 Schema check complete!")
        print(f"✅ {len(schema_info)} tables analyzed")
        print(f"📄 Schema details saved to actual_database_schema.json")
    else:
        print("❌ Failed to retrieve database schema")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)