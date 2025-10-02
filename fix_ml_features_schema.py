#!/usr/bin/env python3
import mysql.connector

def check_ml_features_schema():
    """Check ml_features_materialized table schema"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor()

    # Get table structure
    cursor.execute("DESCRIBE ml_features_materialized")
    columns = cursor.fetchall()
    
    print(f"ml_features_materialized has {len(columns)} columns:")
    for col in columns:
        print(f"  {col[0]} - {col[1]}")
        
    # Check if we need to add price, open, high, low, close columns
    column_names = [col[0] for col in columns]
    missing_columns = []
    
    needed_columns = [
        ('price', 'DECIMAL(20,8)'),
        ('open', 'DECIMAL(20,8)'), 
        ('high', 'DECIMAL(20,8)'),
        ('low', 'DECIMAL(20,8)'),
        ('close', 'DECIMAL(20,8)')
    ]
    
    for col_name, col_type in needed_columns:
        if col_name not in column_names:
            missing_columns.append((col_name, col_type))
            
    if missing_columns:
        print(f"\n❌ Missing {len(missing_columns)} columns:")
        for col_name, col_type in missing_columns:
            print(f"  Adding {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE ml_features_materialized ADD COLUMN {col_name} {col_type} DEFAULT NULL")
        print("✅ Added missing columns")
        conn.commit()
    else:
        print("\n✅ All required columns present")
        
    conn.close()

if __name__ == "__main__":
    check_ml_features_schema()