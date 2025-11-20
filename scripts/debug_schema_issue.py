#!/usr/bin/env python3
"""
Quick Database Schema Debug
Debug the column mismatch issue in CI database setup.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def debug_schema_issue():
    """Debug the schema mismatch issue"""
    print("🔍 Debugging Schema Issue")
    print("=" * 50)
    
    # Check if we have environment variables
    mysql_host = os.environ.get('MYSQL_HOST', 'unknown')
    mysql_user = os.environ.get('MYSQL_USER', 'unknown') 
    mysql_database = os.environ.get('MYSQL_DATABASE', 'unknown')
    
    print(f"📋 Environment Variables:")
    print(f"   MYSQL_HOST: {mysql_host}")
    print(f"   MYSQL_USER: {mysql_user}")
    print(f"   MYSQL_DATABASE: {mysql_database}")
    
    if mysql_host == 'unknown':
        print("❌ No MySQL environment variables set")
        print("💡 This is just a code analysis - not connecting to database")
        
    print()
    print("🔍 Analyzing init_ci_database.py...")
    
    init_script = PROJECT_ROOT / 'scripts' / 'init_ci_database.py'
    
    with open(init_script, 'r') as f:
        content = f.read()
    
    # Extract CREATE TABLE statement for price_data_real
    lines = content.split('\n')
    in_price_table = False
    price_table_lines = []
    
    for i, line in enumerate(lines):
        if 'CREATE TABLE IF NOT EXISTS price_data_real' in line:
            in_price_table = True
            price_table_lines.append(f"Line {i+1}: {line}")
        elif in_price_table:
            price_table_lines.append(f"Line {i+1}: {line}")
            if line.strip().endswith(');') or line.strip() == ')':
                break
    
    print("📋 price_data_real CREATE TABLE statement:")
    for line in price_table_lines[:15]:  # First 15 lines
        print(f"   {line}")
    
    # Extract INSERT statement for price_data_real
    insert_lines = []
    for i, line in enumerate(lines):
        if 'INSERT IGNORE INTO price_data_real' in line:
            insert_lines.append(f"Line {i+1}: {line}")
            # Get next few lines
            for j in range(1, 6):
                if i + j < len(lines):
                    insert_lines.append(f"Line {i+j+1}: {lines[i+j]}")
                    if lines[i+j].strip().endswith('""")'):
                        break
            break
    
    print()
    print("📋 price_data_real INSERT statement:")
    for line in insert_lines:
        print(f"   {line}")
    
    # Check for column name consistency
    print()
    print("🔍 Column Analysis:")
    
    # Extract column names from CREATE TABLE
    create_columns = []
    for line in price_table_lines:
        line_content = line.split(': ', 1)[1] if ': ' in line else line
        line_content = line_content.strip()
        
        if (line_content and 
            not line_content.startswith('CREATE TABLE') and
            not line_content.startswith('id BIGINT AUTO_INCREMENT') and
            not line_content.startswith('INDEX') and
            not line_content.startswith('UNIQUE') and
            not line_content.startswith(')') and
            not line_content == '' and
            ' ' in line_content):
            
            column_name = line_content.split(' ')[0]
            if column_name and not column_name.startswith('--'):
                create_columns.append(column_name)
    
    print("   CREATE TABLE columns:", create_columns[:10])  # First 10 columns
    
    # Extract column names from INSERT
    insert_columns = []
    for line in insert_lines:
        if 'INSERT IGNORE INTO price_data_real (' in line:
            # Extract column list from INSERT statement
            start = line.find('(') + 1
            end = line.find(')')
            if start > 0 and end > start:
                columns_str = line[start:end]
                insert_columns = [col.strip() for col in columns_str.split(',')]
                break
    
    print("   INSERT columns:", insert_columns)
    
    # Check for mismatches
    missing_in_create = [col for col in insert_columns if col not in create_columns]
    if missing_in_create:
        print(f"❌ Columns in INSERT but not in CREATE: {missing_in_create}")
    else:
        print("✅ All INSERT columns exist in CREATE TABLE")
    
    print()
    print("💡 Possible Issues:")
    print("   1. Table creation might be failing silently")
    print("   2. Different database/connection being used for INSERT")
    print("   3. Table might be created but with different schema")
    print("   4. Column name case sensitivity issue")
    
    print()
    print("🔧 Suggested Solutions:")
    print("   1. Add DESCRIBE table before INSERT in CI script")
    print("   2. Check exact error message and line number")
    print("   3. Verify table was actually created successfully")
    print("   4. Add column existence check before INSERT")
    
if __name__ == "__main__":
    debug_schema_issue()