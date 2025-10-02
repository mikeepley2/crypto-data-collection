#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, date, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def check_recent_records():
    """Check for recent records in materialized table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("=== RECENT RECORDS ANALYSIS ===")
        
        # Check total records and recent records
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """)
        recent_7d = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 1 DAY)
        """)
        recent_1d = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        updated_1h = cursor.fetchone()[0]
        
        # Get date range
        cursor.execute("""
            SELECT MIN(date) as oldest, MAX(date) as newest 
            FROM ml_features_materialized
        """)
        date_range = cursor.fetchone()
        
        print(f"Total Records: {total_records:,}")
        print(f"Date Range: {date_range[0]} to {date_range[1]}")
        print(f"Last 7 days: {recent_7d:,} records")
        print(f"Last 1 day: {recent_1d:,} records") 
        print(f"Updated in last hour: {updated_1h:,} records")
        
        # Check most recent records by symbol
        cursor.execute("""
            SELECT symbol, MAX(date) as latest_date, COUNT(*) as total_records
            FROM ml_features_materialized 
            GROUP BY symbol 
            ORDER BY latest_date DESC 
            LIMIT 10
        """)
        
        recent_by_symbol = cursor.fetchall()
        print(f"\nMost Recently Updated Symbols:")
        for row in recent_by_symbol:
            print(f"  {row[0]}: {row[1]} ({row[2]:,} total records)")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking recent records: {e}")
        return False


def analyze_column_population():
    """Analyze column population rates"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n=== COLUMN POPULATION ANALYSIS ===")
        
        # Get total record count for percentage calculations
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]
        
        # Key columns to check
        key_columns = [
            # Basic data
            'current_price', 'volume_24h', 'price_change_24h',
            # OHLC data  
            'open_price', 'close_price', 'high_price', 'low_price', 'ohlc_volume',
            # Technical indicators
            'sma_7', 'sma_30', 'rsi_14', 'bb_upper', 'bb_lower',
            # Macro indicators
            'vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate',
            # Sentiment data
            'crypto_sentiment_count', 'avg_cryptobert_score',
            # Onchain data
            'total_volume_24h', 'exchange_net_flow_24h'
        ]
        
        print(f"Analyzing {len(key_columns)} key columns from {total_records:,} total records:")
        print()
        
        column_stats = []
        
        for column in key_columns:
            try:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN {column} IS NOT NULL THEN 1 ELSE 0 END) as populated,
                        ROUND(SUM(CASE WHEN {column} IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as percentage
                    FROM ml_features_materialized
                """)
                
                result = cursor.fetchone()
                populated_count = result[1]
                percentage = result[2]
                
                column_stats.append({
                    'column': column,
                    'populated': populated_count,
                    'percentage': percentage
                })
                
                status = "✅" if percentage > 80 else "⚠️" if percentage > 50 else "❌"
                print(f"{status} {column:25} {populated_count:>8,} / {total_records:,} ({percentage:>6.2f}%)")
                
            except Exception as e:
                print(f"❌ {column:25} ERROR: {str(e)[:50]}")
        
        # Summary statistics
        print(f"\n=== SUMMARY STATISTICS ===")
        populated_columns = [col for col in column_stats if col['percentage'] > 80]
        partial_columns = [col for col in column_stats if 50 <= col['percentage'] <= 80]
        empty_columns = [col for col in column_stats if col['percentage'] < 50]
        
        print(f"Well Populated (>80%): {len(populated_columns)} columns")
        print(f"Partially Populated (50-80%): {len(partial_columns)} columns")
        print(f"Low Population (<50%): {len(empty_columns)} columns")
        
        avg_population = sum(col['percentage'] for col in column_stats) / len(column_stats)
        print(f"Average Population Rate: {avg_population:.2f}%")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing column population: {e}")
        return False


def check_recent_updates_by_hour():
    """Check recent updates by hour to see continuous processing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n=== RECENT UPDATE ACTIVITY ===")
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(updated_at, '%Y-%m-%d %H:00') as hour_bucket,
                COUNT(*) as updates,
                COUNT(DISTINCT symbol) as symbols_updated
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
            GROUP BY hour_bucket
            ORDER BY hour_bucket DESC
        """)
        
        hourly_updates = cursor.fetchall()
        
        if hourly_updates:
            print("Updates by hour (last 6 hours):")
            for row in hourly_updates:
                print(f"  {row[0]}: {row[1]:,} updates, {row[2]} symbols")
        else:
            print("No recent updates found in last 6 hours")
            
        # Check latest updated records
        cursor.execute("""
            SELECT symbol, date, updated_at, 
                   CASE WHEN open_price IS NOT NULL THEN 'Y' ELSE 'N' END as has_ohlc,
                   CASE WHEN vix IS NOT NULL THEN 'Y' ELSE 'N' END as has_macro
            FROM ml_features_materialized 
            ORDER BY updated_at DESC 
            LIMIT 10
        """)
        
        latest_updates = cursor.fetchall()
        print(f"\nLatest 10 updated records:")
        print("Symbol    Date        Updated              OHLC Macro")
        print("-" * 55)
        for row in latest_updates:
            print(f"{row[0]:8} {row[1]} {row[2]} {row[3]:4} {row[4]:5}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking recent updates: {e}")
        return False


def main():
    """Main function to run all checks"""
    logger.info("Starting materialized table analysis...")
    
    print("🔍 MATERIALIZED TABLE COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    
    success = True
    
    # Run all checks
    if not check_recent_records():
        success = False
        
    if not analyze_column_population():
        success = False
        
    if not check_recent_updates_by_hour():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ANALYSIS COMPLETED SUCCESSFULLY")
    else:
        print("❌ SOME ANALYSIS CHECKS FAILED")
        
    return success


if __name__ == "__main__":
    main()

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

print('=== MATERIALIZED TABLE POPULATION STATUS ===')

# Recent activity check
cursor.execute('''
    SELECT 
        COUNT(DISTINCT symbol) as symbols,
        COUNT(*) as total_records,
        MAX(timestamp_iso) as latest_update,
        TIMESTAMPDIFF(MINUTE, MAX(timestamp_iso), NOW()) as minutes_since_update
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
''')
recent = cursor.fetchone()
print(f'Last Hour: {recent[0]} symbols, {recent[1]} records, latest: {recent[2]}, {recent[3]} mins ago')

# Symbol coverage check
cursor.execute('''
    SELECT symbol, COUNT(*) as records, MAX(timestamp_iso) as latest 
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
    GROUP BY symbol 
    ORDER BY records DESC 
    LIMIT 10
''')
top_symbols = cursor.fetchall()
print('Top 10 Most Active Symbols (Last 2 hours):')
for symbol, count, latest in top_symbols:
    print(f'  {symbol}: {count} records, latest: {latest}')

# Check feature completeness
cursor.execute('''
    SELECT 
        symbol,
        COUNT(*) as records,
        COUNT(current_price) as has_price,
        COUNT(rsi_14) as has_rsi,
        COUNT(avg_cryptobert_score) as has_sentiment,
        COUNT(vwap) as has_vwap,
        MAX(timestamp_iso) as latest
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
    GROUP BY symbol
    ORDER BY records DESC
    LIMIT 15
''')
feature_check = cursor.fetchall()
print('\nFeature Completeness Check (Last 6 hours):')
print('Symbol       Records  Price  RSI   Sent  VWAP  Latest Update')
print('-' * 70)
for row in feature_check:
    symbol, records, price, rsi, sentiment, vwap, latest = row
    print(f'{symbol:<12} {records:<8} {price:<6} {rsi:<6} {sentiment:<6} {vwap:<6} {latest}')

# Check data sources
cursor.execute('''
    SELECT 
        'Price Data' as source,
        COUNT(DISTINCT symbol) as symbols_covered,
        COUNT(*) as records,
        AVG(CASE WHEN current_price IS NOT NULL THEN 1 ELSE 0 END) * 100 as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    
    UNION ALL
    
    SELECT 
        'Technical Indicators' as source,
        COUNT(DISTINCT CASE WHEN rsi_14 IS NOT NULL THEN symbol END) as symbols_covered,
        COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as records,
        AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) * 100 as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    
    UNION ALL
    
    SELECT 
        'Sentiment Data' as source,
        COUNT(DISTINCT CASE WHEN avg_cryptobert_score IS NOT NULL THEN symbol END) as symbols_covered,
        COUNT(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 END) as records,
        AVG(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) * 100 as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    
    UNION ALL
    
    SELECT 
        'OHLC Data' as source,
        COUNT(DISTINCT CASE WHEN close_price IS NOT NULL THEN symbol END) as symbols_covered,
        COUNT(CASE WHEN close_price IS NOT NULL THEN 1 END) as records,
        AVG(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) * 100 as completeness
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
''')

sources = cursor.fetchall()
print('\nData Source Coverage (Last 1 hour):')
print('Source               Symbols  Records    Completeness')
print('-' * 55)
for source, symbols, records, completeness in sources:
    print(f'{source:<20} {symbols:<8} {records:<10} {completeness:.1f}%')

# Check for symbols needing attention
cursor.execute('''
    SELECT 
        symbol,
        TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_since_last,
        COUNT(*) as records_last_24h
    FROM ml_features_materialized 
    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY symbol
    HAVING hours_since_last > 2 OR records_last_24h < 10
    ORDER BY hours_since_last DESC
    LIMIT 20
''')

stale_symbols = cursor.fetchall()
if stale_symbols:
    print('\nSymbols Needing Attention (Stale or Low Volume):')
    print('Symbol       Hours Old  Records (24h)')
    print('-' * 35)
    for symbol, hours_old, records in stale_symbols:
        print(f'{symbol:<12} {hours_old:<10} {records}')
else:
    print('\n✅ All symbols are being updated regularly!')

conn.close()
print('\n=== STATUS CHECK COMPLETE ===')