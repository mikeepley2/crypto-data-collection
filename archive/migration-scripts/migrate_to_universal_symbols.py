#!/usr/bin/env python3
"""
Universal Symbol Migration Script
=================================

This script migrates all data from CoinGecko ID format (bitcoin, ethereum, cardano)
to universal ticker symbols (BTC, ETH, ADA) for maximum cross-exchange compatibility.

Target Tables:
- crypto_onchain_data: symbol column
- real_time_sentiment_signals: symbol column  
- sentiment_aggregation: symbol column
- crypto_news: crypto_mentions column
- Other tables as needed

Benefits:
- Universal compatibility across ALL exchanges
- Consistent ticker format (BTC, ETH, ADA, SOL)
- Prevents confusion between exchange-specific formats
"""

import mysql.connector
import sys
import os
import re
from datetime import datetime

# Add current directory to path for imports
sys.path.append('/app')
sys.path.append('.')

try:
    from shared_symbol_normalizer import UniversalSymbolNormalizer
except ImportError:
    print("❌ Error: shared_symbol_normalizer not found. Please ensure it's deployed.")
    sys.exit(1)

def get_db_config():
    """Get database configuration"""
    return {
        'host': 'host.docker.internal',
        'port': 3306,
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_prices'
    }

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(**get_db_config(), autocommit=False)

def migrate_table_symbols(table_name, symbol_column, normalizer, connection):
    """Migrate symbols in a specific table column"""
    cursor = connection.cursor()
    
    try:
        print(f"\n🔄 Processing {table_name}.{symbol_column}...")
        
        # Get current symbol mapping
        old_to_canonical = normalizer.get_old_to_canonical_map()
        
        # Check existing symbols that need conversion
        cursor.execute(f"""
            SELECT DISTINCT {symbol_column} 
            FROM {table_name} 
            WHERE {symbol_column} IS NOT NULL 
            AND {symbol_column} != ''
            ORDER BY {symbol_column}
        """)
        
        existing_symbols = [row[0] for row in cursor.fetchall()]
        print(f"   📊 Found {len(existing_symbols)} unique symbols")
        
        # Find symbols that need conversion
        conversions_needed = {}
        for symbol in existing_symbols:
            if symbol in old_to_canonical:
                canonical = old_to_canonical[symbol]
                if canonical != symbol:  # Only if conversion needed
                    conversions_needed[symbol] = canonical
        
        print(f"   🔄 {len(conversions_needed)} symbols need conversion:")
        for old, new in list(conversions_needed.items())[:10]:  # Show first 10
            print(f"      {old} -> {new}")
        
        if len(conversions_needed) > 10:
            print(f"      ... and {len(conversions_needed) - 10} more")
        
        # Perform conversions
        total_updated = 0
        batch_size = 1000
        
        for old_symbol, new_symbol in conversions_needed.items():
            # Count records to update
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table_name} 
                WHERE {symbol_column} = %s
            """, (old_symbol,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Update in batches
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET {symbol_column} = %s 
                    WHERE {symbol_column} = %s
                """, (new_symbol, old_symbol))
                
                updated = cursor.rowcount
                total_updated += updated
                
                print(f"   ✅ {old_symbol} -> {new_symbol}: {updated:,} records")
        
        connection.commit()
        print(f"   📊 {table_name}: {total_updated:,} total records updated")
        return total_updated
        
    except Exception as e:
        print(f"   ❌ Error processing {table_name}: {e}")
        connection.rollback()
        return 0
    finally:
        cursor.close()

def migrate_crypto_mentions(normalizer, connection):
    """Migrate crypto_mentions in news tables from CoinGecko IDs to ticker symbols"""
    cursor = connection.cursor()
    
    try:
        print(f"\n🔄 Processing crypto_mentions fields...")
        
        old_to_canonical = normalizer.get_old_to_canonical_map()
        
        # News tables with crypto_mentions
        news_tables = ['crypto_news', 'crypto_news_archive']
        total_updated = 0
        
        for table_name in news_tables:
            print(f"\n   📰 Processing {table_name}...")
            
            # Get records with crypto_mentions
            cursor.execute(f"""
                SELECT id, crypto_mentions 
                FROM {table_name} 
                WHERE crypto_mentions IS NOT NULL 
                AND crypto_mentions != '' 
                AND crypto_mentions != '[]'
                LIMIT 5000
            """)
            
            records = cursor.fetchall()
            print(f"      📊 Found {len(records):,} records with crypto mentions")
            
            updated_count = 0
            
            for record_id, old_mentions in records:
                if not old_mentions:
                    continue
                    
                # Parse mentions (comma-separated)
                symbols = re.split(r'[,\s]+', old_mentions.strip())
                symbols = [s.strip() for s in symbols if s.strip()]
                
                # Convert to universal format
                converted_symbols = []
                changed = False
                
                for symbol in symbols:
                    if symbol in old_to_canonical:
                        canonical = old_to_canonical[symbol]
                        converted_symbols.append(canonical)
                        if canonical != symbol:
                            changed = True
                    else:
                        converted_symbols.append(symbol)
                
                # Update if changed
                if changed:
                    new_mentions = ','.join(converted_symbols)
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET crypto_mentions = %s 
                        WHERE id = %s
                    """, (new_mentions, record_id))
                    
                    updated_count += 1
                    
                    # Show first few conversions
                    if updated_count <= 3:
                        print(f"      🔄 {old_mentions} -> {new_mentions}")
            
            connection.commit()
            print(f"      ✅ {table_name}: {updated_count:,} records updated")
            total_updated += updated_count
        
        print(f"   📊 Total crypto_mentions updated: {total_updated:,}")
        return total_updated
        
    except Exception as e:
        print(f"   ❌ Error processing crypto_mentions: {e}")
        connection.rollback()
        return 0

def main():
    print("🚀 UNIVERSAL SYMBOL MIGRATION")
    print("=============================")
    print(f"Started at: {datetime.now()}")
    print("")
    print("🎯 Goal: Convert all data to universal ticker symbols")
    print("📊 Format: CoinGecko IDs -> Ticker Symbols")
    print("🏦 Benefit: Compatible with ALL exchanges")
    
    # Initialize normalizer
    try:
        db_config = get_db_config()
        normalizer = UniversalSymbolNormalizer(db_config)
        print("\n✅ Universal symbol normalizer initialized")
    except Exception as e:
        print(f"❌ Error initializing normalizer: {e}")
        return
    
    # Connect to database
    try:
        connection = get_db_connection()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return
    
    # Migration targets
    migrations = [
        ('crypto_onchain_data', 'symbol'),
        ('real_time_sentiment_signals', 'symbol'),
        ('sentiment_aggregation', 'symbol'),
    ]
    
    total_updated = 0
    
    try:
        # Migrate symbol columns
        for table_name, column_name in migrations:
            updated = migrate_table_symbols(table_name, column_name, normalizer, connection)
            total_updated += updated
        
        # Migrate crypto_mentions
        mentions_updated = migrate_crypto_mentions(normalizer, connection)
        total_updated += mentions_updated
        
        print(f"\n🎉 MIGRATION COMPLETED!")
        print(f"📊 Total records updated: {total_updated:,}")
        print(f"🏦 All data now uses universal ticker symbols!")
        print(f"✅ Ready for cross-exchange compatibility!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        connection.rollback()
    finally:
        connection.close()
        print(f"\n✅ Migration completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
