#!/usr/bin/env python3
import mysql.connector

def add_macro_columns():
    """Add macro economic columns"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("DESCRIBE ml_features_materialized")
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    # Define macro economic columns
    macro_columns = [
        ('gdp_growth', 'DECIMAL(8,4)'),
        ('cpi_inflation', 'DECIMAL(8,4)'),
        ('interest_rate', 'DECIMAL(8,4)'),
        ('employment_rate', 'DECIMAL(8,4)'),
        ('consumer_confidence', 'DECIMAL(8,4)'),
        ('retail_sales', 'DECIMAL(15,8)'),
        ('industrial_production', 'DECIMAL(8,4)')
    ]
    
    for col_name, col_type in macro_columns:
        if col_name not in existing_columns:
            print(f"Adding {col_name} ({col_type})")
            try:
                cursor.execute(f"ALTER TABLE ml_features_materialized ADD COLUMN {col_name} {col_type} DEFAULT NULL")
                print(f"✅ Added {col_name}")
            except Exception as e:
                print(f"❌ Error adding {col_name}: {e}")
                
    conn.commit()
    conn.close()
    print("✅ Macro columns update complete")

if __name__ == "__main__":
    add_macro_columns()