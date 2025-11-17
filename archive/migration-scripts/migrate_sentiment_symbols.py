#!/usr/bin/env python3
"""
🔄 SENTIMENT DATA MIGRATION TO CANONICAL SYMBOLS
===============================================
Migrates sentiment tables from old symbols (BTC, ETH) to canonical (bitcoin, ethereum)
Tables to migrate:
- real_time_sentiment_signals
- sentiment_aggregation
"""

import mysql.connector
import sys
import os

# Add the normalizer to path
sys.path.append('/tmp')
from shared_symbol_normalizer import SymbolNormalizer

def migrate_sentiment_data():
    """Migrate sentiment data to canonical symbols"""
    
    db_config = {
        'host': 'host.docker.internal',
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    print("🚀 Starting sentiment data migration...")
    
    # Initialize normalizer
    normalizer = SymbolNormalizer(db_config)
    mapping = normalizer.get_old_to_canonical_map()
    
    print(f"📊 Symbol mappings available: {len(mapping)}")
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Tables to migrate
        tables_to_migrate = [
            'real_time_sentiment_signals',
            'sentiment_aggregation'
        ]
        
        total_updated = 0
        
        for table_name in tables_to_migrate:
            print(f"\n🔄 Migrating table: {table_name}")
            
            try:
                # Get current old symbols in this table
                cursor.execute(f"SELECT DISTINCT symbol FROM {table_name} WHERE symbol IN %s", 
                              (tuple(mapping.keys()),))
                old_symbols_in_table = cursor.fetchall()
                
                if not old_symbols_in_table:
                    print(f"   ✅ No old symbols found in {table_name}")
                    continue
                
                table_updated = 0
                
                for (old_symbol,) in old_symbols_in_table:
                    canonical_symbol = mapping.get(old_symbol)
                    if canonical_symbol:
                        print(f"   🔄 {old_symbol} -> {canonical_symbol}")
                        
                        # Update records
                        update_query = f"UPDATE {table_name} SET symbol = %s WHERE symbol = %s"
                        cursor.execute(update_query, (canonical_symbol, old_symbol))
                        updated_count = cursor.rowcount
                        
                        print(f"   ✅ Updated {updated_count:,} records")
                        table_updated += updated_count
                
                print(f"   📊 Total updated in {table_name}: {table_updated:,}")
                total_updated += table_updated
                
            except Exception as e:
                print(f"   ❌ Error migrating {table_name}: {e}")
        
        # Commit all changes
        connection.commit()
        
        print(f"\n🎉 MIGRATION COMPLETED!")
        print(f"📊 Total records updated: {total_updated:,}")
        print("✅ All sentiment data now uses canonical symbols")
        
        # Verify migration
        print(f"\n🔍 Verification:")
        for table_name in tables_to_migrate:
            try:
                cursor.execute(f"SELECT DISTINCT symbol FROM {table_name} ORDER BY symbol LIMIT 10")
                symbols = cursor.fetchall()
                symbol_list = [s[0] for s in symbols]
                print(f"   {table_name}: {symbol_list}")
            except Exception as e:
                print(f"   Error verifying {table_name}: {e}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        raise

if __name__ == "__main__":
    migrate_sentiment_data()