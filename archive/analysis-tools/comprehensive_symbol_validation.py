#!/usr/bin/env python3
"""
Comprehensive Crypto Assets Symbol Validation & Normalization
Validates all symbols in crypto_assets table and across all collection tables
"""

import mysql.connector
import json
import os
from datetime import datetime
from collections import defaultdict
import sys

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
from table_config import (
    PRIMARY_COLLECTION_TABLES, 
    normalize_symbol_to_internal,
    validate_symbol,
    EXCHANGE_FORMATS,
    get_symbol_registry_table,
    get_active_symbols_query,
    get_coinbase_symbols_query
)

def get_db_connection():
    """Get database connection using environment variables or defaults"""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "172.22.32.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "news_collector"),
        password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
        database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
        autocommit=True,
        charset='utf8mb4'
    )

def analyze_crypto_assets_table():
    """Analyze the crypto_assets table structure and data quality"""
    print("🔍 CRYPTO ASSETS TABLE ANALYSIS")
    print("=" * 80)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Table schema analysis
    print("\n📋 TABLE SCHEMA:")
    cursor.execute(f"DESCRIBE {get_symbol_registry_table()}")
    schema = cursor.fetchall()
    for field in schema:
        nullable = "NULL" if field['Null'] == 'YES' else "NOT NULL"
        key_info = f" ({field['Key']})" if field['Key'] else ""
        print(f"   {field['Field']:<20}: {field['Type']:<20} {nullable}{key_info}")
    
    # 2. Data overview
    print(f"\n📊 DATA OVERVIEW:")
    cursor.execute(f"SELECT COUNT(*) as total FROM {get_symbol_registry_table()}")
    total_assets = cursor.fetchone()['total']
    
    cursor.execute(f"SELECT COUNT(*) as active FROM {get_symbol_registry_table()} WHERE is_active = 1")
    active_assets = cursor.fetchone()['active']
    
    cursor.execute(f"SELECT COUNT(*) as coinbase FROM {get_symbol_registry_table()} WHERE coinbase_supported = 1")
    coinbase_assets = cursor.fetchone()['coinbase']
    
    cursor.execute(f"SELECT COUNT(*) as with_coingecko FROM {get_symbol_registry_table()} WHERE coingecko_id IS NOT NULL AND coingecko_id != ''")
    coingecko_assets = cursor.fetchone()['with_coingecko']
    
    print(f"   Total Assets:      {total_assets:,}")
    print(f"   Active Assets:     {active_assets:,}")
    print(f"   Coinbase Support:  {coinbase_assets:,}")
    print(f"   CoinGecko IDs:     {coingecko_assets:,}")
    
    # 3. Symbol format analysis
    print(f"\n🔧 SYMBOL FORMAT ANALYSIS:")
    cursor.execute(f"""
        SELECT 
            symbol,
            LENGTH(symbol) as symbol_length,
            CASE 
                WHEN symbol LIKE '%-%' THEN 'contains_dash'
                WHEN symbol LIKE '%_%' THEN 'contains_underscore'  
                WHEN symbol LIKE '%/%' THEN 'contains_slash'
                WHEN symbol REGEXP '[^A-Z0-9]' THEN 'invalid_chars'
                WHEN NOT symbol LIKE '%USD' THEN 'no_usd_suffix'
                ELSE 'valid_format'
            END as format_issue
        FROM {get_symbol_registry_table()}
        WHERE is_active = 1
    """)
    
    format_issues = defaultdict(list)
    for row in cursor.fetchall():
        format_issues[row['format_issue']].append(row['symbol'])
    
    for issue_type, symbols in format_issues.items():
        print(f"   {issue_type.upper():<20}: {len(symbols):,} symbols")
        if len(symbols) <= 10 and issue_type != 'valid_format':
            print(f"      Examples: {', '.join(symbols[:5])}")
    
    # 4. Data completeness analysis
    print(f"\n📈 DATA COMPLETENESS:")
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN name IS NOT NULL AND name != '' THEN 1 ELSE 0 END) as has_name,
            SUM(CASE WHEN coingecko_id IS NOT NULL AND coingecko_id != '' THEN 1 ELSE 0 END) as has_coingecko,
            SUM(CASE WHEN aliases IS NOT NULL AND aliases != '' THEN 1 ELSE 0 END) as has_aliases,
            SUM(CASE WHEN coinbase_supported = 1 THEN 1 ELSE 0 END) as coinbase_supported
        FROM {get_symbol_registry_table()}
        WHERE is_active = 1
    """)
    
    completeness = cursor.fetchone()
    total = completeness['total']
    print(f"   Active Assets:         {total:,}")
    print(f"   With Names:            {completeness['has_name']:,} ({completeness['has_name']/total*100:.1f}%)")
    print(f"   With CoinGecko IDs:    {completeness['has_coingecko']:,} ({completeness['has_coingecko']/total*100:.1f}%)")
    print(f"   With Aliases:          {completeness['has_aliases']:,} ({completeness['has_aliases']/total*100:.1f}%)")
    print(f"   Coinbase Supported:    {completeness['coinbase_supported']:,} ({completeness['coinbase_supported']/total*100:.1f}%)")
    
    cursor.close()
    conn.close()
    
    return format_issues

def validate_symbol_normalization():
    """Validate symbol normalization across the crypto_assets table"""
    print("\n🔧 SYMBOL NORMALIZATION VALIDATION")
    print("=" * 80)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all active symbols
    cursor.execute(get_active_symbols_query())
    symbols = [row['symbol'] for row in cursor.fetchall()]
    
    print(f"\n📊 Validating {len(symbols):,} active symbols...")
    
    validation_results = {
        'valid': [],
        'invalid': [],
        'normalization_needed': []
    }
    
    for symbol in symbols:
        result = validate_symbol(symbol)
        
        if result['valid']:
            validation_results['valid'].append(symbol)
        else:
            validation_results['invalid'].append({
                'symbol': symbol,
                'issues': result['issues']
            })
        
        # Check if normalization would change the symbol
        normalized = normalize_symbol_to_internal(symbol)
        if normalized != symbol:
            validation_results['normalization_needed'].append({
                'original': symbol,
                'normalized': normalized
            })
    
    print(f"\n✅ VALIDATION RESULTS:")
    print(f"   Valid Symbols:              {len(validation_results['valid']):,}")
    print(f"   Invalid Symbols:            {len(validation_results['invalid']):,}")
    print(f"   Need Normalization:         {len(validation_results['normalization_needed']):,}")
    
    # Show invalid symbols
    if validation_results['invalid']:\n        print(f"\n❌ INVALID SYMBOLS:\")\n        for item in validation_results['invalid'][:10]:\n            print(f\"   {item['symbol']}: {', '.join(item['issues'])}\")\n        if len(validation_results['invalid']) > 10:\n            print(f\"   ... and {len(validation_results['invalid']) - 10} more\")\n    \n    # Show normalization needed\n    if validation_results['normalization_needed']:\n        print(f\"\\n🔧 SYMBOLS NEEDING NORMALIZATION:\")\n        for item in validation_results['normalization_needed'][:10]:\n            print(f\"   {item['original']} -> {item['normalized']}\")\n        if len(validation_results['normalization_needed']) > 10:\n            print(f\"   ... and {len(validation_results['normalization_needed']) - 10} more\")\n    \n    cursor.close()\n    conn.close()\n    \n    return validation_results\n\ndef analyze_symbol_usage_across_tables():\n    \"\"\"Analyze symbol usage across all primary collection tables\"\"\"\n    print(\"\\n📊 SYMBOL USAGE ACROSS COLLECTION TABLES\")\n    print(\"=\" * 80)\n    \n    # Skip the assets table itself\n    collection_tables = {k: v for k, v in PRIMARY_COLLECTION_TABLES.items() if k != 'ASSETS' and k != 'MONITORING'}\n    \n    symbol_usage = {}\n    conn = get_db_connection()\n    \n    for table_type, full_table_name in collection_tables.items():\n        try:\n            # Split database.table format\n            if '.' in full_table_name:\n                database, table_name = full_table_name.split('.', 1)\n                cursor = conn.cursor()\n                cursor.execute(f\"USE {database}\")\n                cursor = conn.cursor(dictionary=True)\n            else:\n                cursor = conn.cursor(dictionary=True)\n                table_name = full_table_name\n            \n            # Try different common column names for symbols\n            symbol_columns = ['symbol', 'coin_symbol', 'asset', 'ticker']\n            symbol_col = None\n            \n            for col in symbol_columns:\n                try:\n                    cursor.execute(f\"SELECT {col} FROM {table_name} LIMIT 1\")\n                    symbol_col = col\n                    break\n                except mysql.connector.Error:\n                    continue\n            \n            if symbol_col:\n                cursor.execute(f\"\"\"\n                    SELECT \n                        {symbol_col} as symbol,\n                        COUNT(*) as record_count,\n                        MIN(timestamp) as earliest_date,\n                        MAX(timestamp) as latest_date\n                    FROM {table_name} \n                    WHERE {symbol_col} IS NOT NULL\n                    GROUP BY {symbol_col}\n                    ORDER BY record_count DESC\n                    LIMIT 50\n                \"\"\")\n                \n                results = cursor.fetchall()\n                \n                symbol_usage[table_type] = {\n                    'table': full_table_name,\n                    'symbol_column': symbol_col,\n                    'unique_symbols': len(results),\n                    'symbols': results\n                }\n                \n                print(f\"\\n📋 {table_type} ({full_table_name}):\")\n                print(f\"   Symbol Column: {symbol_col}\")\n                print(f\"   Unique Symbols: {len(results):,}\")\n                \n                if results:\n                    total_records = sum(r['record_count'] for r in results)\n                    print(f\"   Total Records: {total_records:,}\")\n                    \n                    # Show top symbols\n                    print(f\"   Top Symbols:\")\n                    for i, result in enumerate(results[:5], 1):\n                        print(f\"      {i}. {result['symbol']}: {result['record_count']:,} records\")\n            else:\n                print(f\"\\n❌ {table_type} ({full_table_name}): No symbol column found\")\n                symbol_usage[table_type] = {'error': 'No symbol column found'}\n            \n            cursor.close()\n            \n        except Exception as e:\n            print(f\"\\n❌ {table_type} ({full_table_name}): Error - {e}\")\n            symbol_usage[table_type] = {'error': str(e)}\n    \n    conn.close()\n    \n    return symbol_usage\n\ndef cross_validate_symbol_consistency():\n    \"\"\"Cross-validate symbols between crypto_assets and collection tables\"\"\"\n    print(\"\\n🔍 CROSS-VALIDATION: SYMBOL CONSISTENCY\")\n    print(\"=\" * 80)\n    \n    conn = get_db_connection()\n    cursor = conn.cursor(dictionary=True)\n    \n    # Get reference symbols from crypto_assets\n    cursor.execute(get_active_symbols_query())\n    reference_symbols = set(row['symbol'] for row in cursor.fetchall())\n    \n    print(f\"\\n📊 Reference symbols from crypto_assets: {len(reference_symbols):,}\")\n    \n    # Check each collection table\n    collection_symbols = {}\n    \n    # Price data\n    try:\n        cursor.execute(\"SELECT DISTINCT symbol FROM crypto_prices.price_data_real WHERE symbol IS NOT NULL\")\n        price_symbols = set(row['symbol'] for row in cursor.fetchall())\n        collection_symbols['PRICE_DATA'] = price_symbols\n        print(f\"   Price data symbols: {len(price_symbols):,}\")\n    except Exception as e:\n        print(f\"   Price data error: {e}\")\n    \n    # Technical indicators\n    try:\n        cursor.execute(\"SELECT DISTINCT symbol FROM crypto_prices.technical_indicators WHERE symbol IS NOT NULL\")\n        tech_symbols = set(row['symbol'] for row in cursor.fetchall())\n        collection_symbols['TECHNICAL'] = tech_symbols\n        print(f\"   Technical symbols: {len(tech_symbols):,}\")\n    except Exception as e:\n        print(f\"   Technical data error: {e}\")\n    \n    # Onchain data\n    try:\n        cursor.execute(\"SELECT DISTINCT coin_symbol FROM crypto_prices.crypto_onchain_data WHERE coin_symbol IS NOT NULL\")\n        onchain_symbols = set(row['coin_symbol'] for row in cursor.fetchall())\n        collection_symbols['ONCHAIN'] = onchain_symbols\n        print(f\"   Onchain symbols: {len(onchain_symbols):,}\")\n    except Exception as e:\n        print(f\"   Onchain data error: {e}\")\n    \n    # Sentiment data\n    try:\n        cursor.execute(\"SELECT DISTINCT symbol FROM crypto_prices.real_time_sentiment_signals WHERE symbol IS NOT NULL\")\n        sentiment_symbols = set(row['symbol'] for row in cursor.fetchall())\n        collection_symbols['SENTIMENT'] = sentiment_symbols\n        print(f\"   Sentiment symbols: {len(sentiment_symbols):,}\")\n    except Exception as e:\n        print(f\"   Sentiment data error: {e}\")\n    \n    # Analyze consistency\n    print(f\"\\n🔍 CONSISTENCY ANALYSIS:\")\n    \n    for table_name, symbols in collection_symbols.items():\n        if symbols:\n            # Symbols in collection but not in crypto_assets\n            orphaned = symbols - reference_symbols\n            # Symbols in crypto_assets but not in collection\n            missing = reference_symbols - symbols\n            \n            print(f\"\\n   {table_name}:\")\n            print(f\"      Common symbols: {len(symbols & reference_symbols):,}\")\n            \n            if orphaned:\n                print(f\"      Orphaned symbols: {len(orphaned):,}\")\n                if len(orphaned) <= 10:\n                    print(f\"         {', '.join(sorted(orphaned))}\")\n                else:\n                    print(f\"         {', '.join(sorted(list(orphaned)[:10]))} ... and {len(orphaned)-10} more\")\n            \n            if missing:\n                print(f\"      Missing symbols: {len(missing):,}\")\n                if len(missing) <= 10:\n                    print(f\"         {', '.join(sorted(missing))}\")\n                else:\n                    print(f\"         {', '.join(sorted(list(missing)[:10]))} ... and {len(missing)-10} more\")\n    \n    cursor.close()\n    conn.close()\n    \n    return reference_symbols, collection_symbols\n\ndef generate_symbol_normalization_plan():\n    \"\"\"Generate a plan to normalize all symbols across the system\"\"\"\n    print(\"\\n📋 SYMBOL NORMALIZATION PLAN\")\n    print(\"=\" * 80)\n    \n    plan = {\n        'timestamp': datetime.now().isoformat(),\n        'actions': [],\n        'priority': 'HIGH',\n        'estimated_impact': 'All collection tables'\n    }\n    \n    print(f\"\\n🎯 RECOMMENDED ACTIONS:\")\n    \n    # Action 1: Fix crypto_assets table symbols\n    action1 = {\n        'action': 'Normalize symbols in crypto_assets table',\n        'description': 'Update any symbols that don\\'t follow BASEUSD format',\n        'sql': f\"\"\"\n            UPDATE {get_symbol_registry_table()}\n            SET symbol = UPPER(REPLACE(REPLACE(symbol, '-', ''), '/', ''))\n            WHERE symbol LIKE '%-%' OR symbol LIKE '%/%' OR symbol != UPPER(symbol);\n        \"\"\",\n        'risk': 'LOW - Only formatting changes',\n        'verification': 'Check symbol format compliance after update'\n    }\n    plan['actions'].append(action1)\n    print(f\"   1. {action1['description']}\")\n    print(f\"      Risk: {action1['risk']}\")\n    \n    # Action 2: Add missing USD suffixes\n    action2 = {\n        'action': 'Ensure all symbols end with USD',\n        'description': 'Add USD suffix to symbols missing it',\n        'sql': f\"\"\"\n            UPDATE {get_symbol_registry_table()}\n            SET symbol = CONCAT(symbol, 'USD')\n            WHERE symbol NOT LIKE '%USD' AND is_active = 1;\n        \"\"\",\n        'risk': 'MEDIUM - Changes symbol format',\n        'verification': 'Verify all active symbols end with USD'\n    }\n    plan['actions'].append(action2)\n    print(f\"   2. {action2['description']}\")\n    print(f\"      Risk: {action2['risk']}\")\n    \n    # Action 3: Cross-table symbol updates\n    action3 = {\n        'action': 'Update collection tables with normalized symbols',\n        'description': 'Apply normalization to all collection tables',\n        'tables_affected': list(PRIMARY_COLLECTION_TABLES.keys()),\n        'risk': 'HIGH - Affects historical data',\n        'backup_required': True,\n        'verification': 'Full data integrity check required'\n    }\n    plan['actions'].append(action3)\n    print(f\"   3. {action3['description']}\")\n    print(f\"      Risk: {action3['risk']}\")\n    print(f\"      Backup Required: {action3['backup_required']}\")\n    \n    # Action 4: Update collector configurations\n    action4 = {\n        'action': 'Update collector symbol queries',\n        'description': 'Ensure all collectors use normalized symbols',\n        'files_affected': ['k8s configs', 'collector Python scripts'],\n        'risk': 'MEDIUM - May affect data collection',\n        'testing_required': True\n    }\n    plan['actions'].append(action4)\n    print(f\"   4. {action4['description']}\")\n    print(f\"      Risk: {action4['risk']}\")\n    \n    print(f\"\\n⚠️  IMPLEMENTATION NOTES:\")\n    print(f\"   • Execute actions in order (1 → 2 → 3 → 4)\")\n    print(f\"   • Test each action on a backup/staging environment first\")\n    print(f\"   • Monitor data collection after symbol updates\")\n    print(f\"   • Maintain exchange format conversion functions\")\n    \n    return plan\n\ndef main():\n    \"\"\"Main execution function\"\"\"\n    print(\"🚀 COMPREHENSIVE SYMBOL VALIDATION & NORMALIZATION\")\n    print(f\"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n    print(\"=\" * 80)\n    \n    try:\n        # 1. Analyze crypto_assets table\n        format_issues = analyze_crypto_assets_table()\n        \n        # 2. Validate symbol normalization\n        validation_results = validate_symbol_normalization()\n        \n        # 3. Analyze symbol usage across tables\n        symbol_usage = analyze_symbol_usage_across_tables()\n        \n        # 4. Cross-validate symbol consistency\n        reference_symbols, collection_symbols = cross_validate_symbol_consistency()\n        \n        # 5. Generate normalization plan\n        plan = generate_symbol_normalization_plan()\n        \n        print(f\"\\n✅ ANALYSIS COMPLETED SUCCESSFULLY\")\n        print(f\"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n        \n        # Save results to file\n        results_file = f\"symbol_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\"\n        results = {\n            'timestamp': datetime.now().isoformat(),\n            'format_issues': {k: len(v) for k, v in format_issues.items()},\n            'validation_summary': {\n                'valid_symbols': len(validation_results['valid']),\n                'invalid_symbols': len(validation_results['invalid']), \n                'normalization_needed': len(validation_results['normalization_needed'])\n            },\n            'symbol_usage_summary': {k: v.get('unique_symbols', 0) for k, v in symbol_usage.items()},\n            'normalization_plan': plan\n        }\n        \n        with open(results_file, 'w') as f:\n            json.dump(results, f, indent=2)\n        \n        print(f\"\\n📄 Results saved to: {results_file}\")\n        \n    except Exception as e:\n        print(f\"\\n❌ ERROR: {e}\")\n        raise\n\nif __name__ == \"__main__\":\n    main()\n