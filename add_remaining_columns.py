#!/usr/bin/env python3
import mysql.connector

def add_remaining_columns():
    """Add all remaining columns needed by enhanced materialized updater"""
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
    
    # Define all columns the enhanced updater tries to use
    needed_columns = [
        ('volume_qty_24h', 'DECIMAL(25,2)'),
        ('volume_24h_usd', 'DECIMAL(25,2)'),
        ('percent_change_1h', 'DECIMAL(10,4)'),
        ('percent_change_24h', 'DECIMAL(10,4)'), 
        ('percent_change_7d', 'DECIMAL(10,4)'),
        ('sentiment_positive', 'DECIMAL(8,6)'),
        ('sentiment_negative', 'DECIMAL(8,6)'),
        ('sentiment_neutral', 'DECIMAL(8,6)'),
        ('sentiment_fear_greed_index', 'DECIMAL(8,6)'),
        ('sentiment_volume_weighted', 'DECIMAL(8,6)'),
        ('sentiment_social_dominance', 'DECIMAL(8,6)'),
        ('sentiment_news_impact', 'DECIMAL(8,6)'),
        ('sentiment_whale_movement', 'DECIMAL(8,6)'),
        ('onchain_active_addresses', 'BIGINT'),
        ('onchain_transaction_volume', 'DECIMAL(25,8)'),
        ('onchain_avg_transaction_value', 'DECIMAL(20,8)'),
        ('onchain_nvt_ratio', 'DECIMAL(15,8)'),
        ('onchain_mvrv_ratio', 'DECIMAL(15,8)'),
        ('onchain_whale_transactions', 'INT')
    ]
    
    missing_columns = []
    for col_name, col_type in needed_columns:
        if col_name not in existing_columns:
            missing_columns.append((col_name, col_type))
            
    if missing_columns:
        print(f"❌ Adding {len(missing_columns)} missing columns:")
        for col_name, col_type in missing_columns:
            print(f"  Adding {col_name} ({col_type})")
            try:
                cursor.execute(f"ALTER TABLE ml_features_materialized ADD COLUMN {col_name} {col_type} DEFAULT NULL")
            except Exception as e:
                print(f"    Error adding {col_name}: {e}")
        print("✅ Attempted to add all missing columns")
        conn.commit()
    else:
        print("✅ All columns already present")
        
    conn.close()

if __name__ == "__main__":
    add_remaining_columns()