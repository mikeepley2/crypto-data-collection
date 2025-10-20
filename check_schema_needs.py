#!/usr/bin/env python3
"""Check database schema and identify what needs to change for collectors"""

import mysql.connector
import sys

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="news_collector",
        password="99Rules!",
        database="crypto_prices"
    )
    cursor = conn.cursor(dictionary=True)
    
    # Check existing tables
    print("=" * 70)
    print("EXISTING TABLES IN crypto_prices DATABASE")
    print("=" * 70)
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    existing_tables = [t[list(t.keys())[0]] for t in tables]
    
    for table in sorted(existing_tables):
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()['cnt']
            print(f"  [OK] {table:<35} ({count:>10,} records)")
        except:
            # Skip views or tables with issues
            print(f"  [--] {table:<35} (view or inaccessible)")
    
    print("\n" + "=" * 70)
    print("SCHEMA REQUIREMENTS FOR COLLECTORS")
    print("=" * 70)
    
    # Define what collectors need
    requirements = {
        "macro_indicators": {
            "columns": ["id", "indicator_name", "timestamp", "value", "source", "created_at", "updated_at"],
            "status": "macro_indicators" in existing_tables,
            "purpose": "Store macroeconomic indicators (GDP, inflation, VIX, etc)"
        },
        "onchain_metrics": {
            "columns": ["id", "symbol", "timestamp", "active_addresses", "transaction_count", "transaction_volume", "miner_revenue", "exchange_inflow", "exchange_outflow", "created_at", "updated_at"],
            "status": "onchain_metrics" in existing_tables,
            "purpose": "Store blockchain metrics (Bitcoin, Ethereum)"
        },
        "technical_indicators": {
            "columns": ["id", "symbol", "timestamp", "sma_20", "sma_50", "rsi", "macd", "bb_upper", "bb_lower", "created_at", "updated_at"],
            "status": "technical_indicators" in existing_tables,
            "purpose": "Store technical analysis indicators"
        },
        "crypto_assets": {
            "columns": ["symbol", "name", "active", "created_at", "updated_at"],
            "status": "crypto_assets" in existing_tables,
            "purpose": "Asset configuration (used by onchain collector)"
        }
    }
    
    for table_name, info in requirements.items():
        status_text = "[EXISTS]" if info['status'] else "[MISSING]"
        print(f"\n{status_text} {table_name:<30}")
        print(f"    Purpose: {info['purpose']}")
        
        if info['status']:
            # Show column info
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            col_names = [c['Field'] for c in columns]
            print(f"    Columns: {', '.join(col_names)}")
        else:
            print(f"    Need columns: {', '.join(info['columns'])}")
    
    # Check what we need to create
    missing = [name for name, info in requirements.items() if not info['status']]
    
    if missing:
        print("\n" + "=" * 70)
        print("ACTION REQUIRED: CREATE MISSING TABLES")
        print("=" * 70)
        print(f"\nNeed to CREATE {len(missing)} tables:")
        for table in missing:
            print(f"  - {table}")
    else:
        print("\n" + "=" * 70)
        print("ALL REQUIRED TABLES EXIST!")
        print("=" * 70)
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
