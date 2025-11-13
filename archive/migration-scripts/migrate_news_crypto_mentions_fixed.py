#!/usr/bin/env python3
"""
Migration Script: Normalize crypto_mentions in News Tables
"""

import mysql.connector
import sys
import os
import re
from datetime import datetime

# Add current directory to path for imports
sys.path.append('/app')

try:
    from shared_symbol_normalizer import SymbolNormalizer
except ImportError:
    print("❌ Error: shared_symbol_normalizer not found. Please ensure it's deployed to /app/")
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

def normalize_crypto_mentions(crypto_mentions_str, normalizer):
    """
    Normalize a crypto_mentions string from old format to canonical
    """
    if not crypto_mentions_str or crypto_mentions_str.strip() == '' or crypto_mentions_str == '[]':
        return crypto_mentions_str
    
    # Handle various separators and clean the string
    symbols = re.split(r'[,\s]+', crypto_mentions_str.strip())
    symbols = [s.strip().upper() for s in symbols if s.strip()]
    
    # Get canonical mapping
    old_to_canonical = normalizer.get_old_to_canonical_map()
    
    normalized_symbols = []
    for symbol in symbols:
        # Try direct mapping first
        if symbol in old_to_canonical:
            canonical = old_to_canonical[symbol]
            normalized_symbols.append(canonical)
        # Check common variations
        elif symbol == 'BITCOIN':
            normalized_symbols.append('bitcoin')
        elif symbol == 'ETHEREUM':
            normalized_symbols.append('ethereum')
        elif symbol == 'CARDANO':
            normalized_symbols.append('cardano')
        elif symbol == 'SOLANA':
            normalized_symbols.append('solana')
        elif symbol == 'CHAINLINK':
            normalized_symbols.append('chainlink')
        elif symbol == 'DOGECOIN':
            normalized_symbols.append('dogecoin')
        elif symbol == 'AVALANCHE':
            normalized_symbols.append('avalanche-2')
        elif symbol == 'POLKADOT':
            normalized_symbols.append('polkadot')
        elif symbol == 'UNISWAP':
            normalized_symbols.append('uniswap')
        elif symbol == 'POLYGON':
            normalized_symbols.append('matic-network')
        else:
            # Keep unmapped symbols as lowercase
            print(f"   ⚠️  Unknown symbol: {symbol}")
            normalized_symbols.append(symbol.lower())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_symbols = []
    for sym in normalized_symbols:
        if sym not in seen:
            seen.add(sym)
            unique_symbols.append(sym)
    
    return ','.join(unique_symbols)

def main():
    print("🚀 CRYPTO NEWS MENTIONS MIGRATION")
    print("==================================")
    
    # Initialize normalizer with db_config
    try:
        db_config = get_db_config()
        normalizer = SymbolNormalizer(db_config)
        print("✅ Symbol normalizer initialized")
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
    
    # Target tables
    target_tables = [
        'crypto_news',
        'crypto_news_archive'
    ]
    
    total_updated = 0
    cursor = connection.cursor()
    
    try:
        for table_name in target_tables:
            print(f"\n🔄 Processing {table_name}...")
            
            # Get records with crypto mentions that need normalization
            cursor.execute(f"""
                SELECT id, crypto_mentions 
                FROM {table_name} 
                WHERE crypto_mentions IS NOT NULL 
                AND crypto_mentions != '' 
                AND crypto_mentions != '[]'
                LIMIT 1000
            """)
            
            records = cursor.fetchall()
            print(f"   📊 Found {len(records):,} records with crypto mentions")
            
            updated_count = 0
            
            for record_id, old_mentions in records:
                # Normalize the mentions
                new_mentions = normalize_crypto_mentions(old_mentions, normalizer)
                
                # Only update if changed
                if new_mentions != old_mentions:
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET crypto_mentions = %s 
                        WHERE id = %s
                    """, (new_mentions, record_id))
                    
                    updated_count += 1
                    
                    # Show progress for first few
                    if updated_count <= 5:
                        print(f"   🔄 {old_mentions} -> {new_mentions}")
            
            connection.commit()
            print(f"   ✅ {table_name}: Updated {updated_count:,} records")
            total_updated += updated_count
        
        print(f"\n🎉 MIGRATION COMPLETED!")
        print(f"📊 Total records updated: {total_updated:,}")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
