#!/usr/bin/env python3
"""
Quick Test - Sample Data Validation
Test the corrected sample data insertion logic.
"""

import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

def validate_sample_data():
    """Validate the sample data insertions match table schemas"""
    print("🔍 Validating Sample Data Schema Alignment")
    print("=" * 55)
    
    init_script = PROJECT_ROOT / 'scripts' / 'init_ci_database.py'
    
    with open(init_script, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find crypto_assets schema
    print("📋 crypto_assets analysis:")
    crypto_create_cols = []
    in_crypto_table = False
    for i, line in enumerate(lines):
        if 'CREATE TABLE IF NOT EXISTS crypto_assets' in line:
            in_crypto_table = True
        elif in_crypto_table:
            line_clean = line.strip()
            if line_clean and ' ' in line_clean and not line_clean.startswith('INDEX') and not line_clean.startswith('UNIQUE') and not line_clean.startswith(')'):
                col_name = line_clean.split(' ')[0]
                if col_name and not col_name.startswith('--'):
                    crypto_create_cols.append(col_name)
            if line_clean.endswith(');') or line_clean == ')':
                break
    
    print(f"   CREATE columns: {crypto_create_cols[:8]}...")  # First 8
    
    # Find crypto_assets INSERT
    crypto_insert_cols = []
    for line in lines:
        if 'INSERT IGNORE INTO crypto_assets (' in line:
            start = line.find('(') + 1
            end = line.find(')')
            if start > 0 and end > start:
                columns_str = line[start:end]
                crypto_insert_cols = [col.strip() for col in columns_str.split(',')]
                break
    
    print(f"   INSERT columns: {crypto_insert_cols}")
    
    # Check alignment
    missing_crypto = [col for col in crypto_insert_cols if col not in crypto_create_cols]
    if missing_crypto:
        print(f"   ❌ Missing in CREATE: {missing_crypto}")
    else:
        print("   ✅ All INSERT columns exist in CREATE")
    
    print()
    
    # Same for price_data_real
    print("📋 price_data_real analysis:")
    price_create_cols = []
    in_price_table = False
    for i, line in enumerate(lines):
        if 'CREATE TABLE IF NOT EXISTS price_data_real' in line:
            in_price_table = True
        elif in_price_table:
            line_clean = line.strip()
            if line_clean and ' ' in line_clean and not line_clean.startswith('INDEX') and not line_clean.startswith('UNIQUE') and not line_clean.startswith(')'):
                col_name = line_clean.split(' ')[0]
                if col_name and not col_name.startswith('--'):
                    price_create_cols.append(col_name)
            if line_clean.endswith(');') or line_clean == ')':
                break
    
    print(f"   CREATE columns: {price_create_cols[:8]}...")  # First 8
    
    # Find price_data_real INSERT
    price_insert_cols = []
    for line in lines:
        if 'INSERT IGNORE INTO price_data_real (' in line:
            start = line.find('(') + 1
            end = line.find(')')
            if start > 0 and end > start:
                columns_str = line[start:end]
                price_insert_cols = [col.strip() for col in columns_str.split(',')]
                break
    
    print(f"   INSERT columns: {price_insert_cols}")
    
    # Check alignment
    missing_price = [col for col in price_insert_cols if col not in price_create_cols]
    if missing_price:
        print(f"   ❌ Missing in CREATE: {missing_price}")
    else:
        print("   ✅ All INSERT columns exist in CREATE")
    
    print()
    print("🎯 Summary:")
    if not missing_crypto and not missing_price:
        print("✅ All sample data INSERTs are aligned with table schemas")
        print("✅ CI database initialization should work correctly")
        print("✅ No more 'Unknown column' errors expected")
    else:
        print("❌ Schema misalignments found - need further fixes")
    
if __name__ == "__main__":
    validate_sample_data()