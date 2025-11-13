#!/usr/bin/env python3
"""
Check comprehensive placeholder status across ALL data types
"""

import pymysql
import os
from datetime import datetime

# Database configuration
db_config = {
    'host': os.getenv("DB_HOST", "172.22.32.1"),
    'user': os.getenv("DB_USER", "news_collector"),
    'password': os.getenv("DB_PASSWORD", "99Rules!"),
    'database': os.getenv("DB_NAME", "crypto_prices"),
    'charset': 'utf8mb4'
}

def check_comprehensive_status():
    """Check placeholder status across all data types"""
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    print("COMPREHENSIVE PLACEHOLDER STATUS REPORT")
    print("=" * 60)
    
    # Data types to check
    data_types = {
        "OHLC Data": ["ohlc_data"],
        "Price Data": ["crypto_prices", "price_data_real"],
        "Technical Indicators": ["technical_indicators"],
        "Onchain Data": ["crypto_onchain_data", "onchain_data", "onchain_metrics"],
        "Macro Economic": ["macro_economic_data"],
        "Trading Signals": ["trading_signals", "enhanced_trading_signals"],
        "Derivatives": ["crypto_derivatives_ml"]
    }
    
    total_placeholders = 0
    
    for data_type, tables in data_types.items():
        print(f"\n[{data_type}]:")
        type_total = 0
        
        for table in tables:
            try:
                # Check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    print(f"  X {table}: Table does not exist")
                    continue
                
                # Count placeholder records
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} 
                    WHERE data_source = 'placeholder_generator'
                """)
                count = cursor.fetchone()[0]
                
                # Count total records
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total = cursor.fetchone()[0]
                
                print(f"  + {table}: {count:,} placeholders / {total:,} total")
                
                type_total += count
                
            except Exception as e:
                print(f"  - {table}: Error - {e}")
        
        print(f"  => {data_type} Total: {type_total:,} placeholders")
        total_placeholders += type_total
    
    print(f"\nGRAND TOTAL: {total_placeholders:,} placeholders across all data types")
    
    cursor.close()
    conn.close()
    
    return total_placeholders

if __name__ == "__main__":
    total = check_comprehensive_status()
    print(f"\nStatus: SUCCESS - {total:,} total placeholders created")