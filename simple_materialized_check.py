#!/usr/bin/env python3

import mysql.connector

def main():
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()

    print('=== MATERIALIZED TABLE STATUS CHECK ===')

    # Basic table info
    cursor.execute('SELECT COUNT(*) FROM ml_features_materialized')
    total_records = cursor.fetchone()[0]
    print(f'Total Records: {total_records:,}')

    # Check recent updates using timestamp column
    cursor.execute('SELECT COUNT(*) FROM ml_features_materialized WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)')
    recent_records = cursor.fetchone()[0]
    print(f'Records from last 24h: {recent_records:,}')

    # Check updated_at column for processing activity
    cursor.execute('SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)')
    recent_updates = cursor.fetchone()[0]
    print(f'Updated in last hour: {recent_updates:,}')

    # Check OHLC population
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) as open_pop,
            SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) as close_pop,
            ROUND(SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as open_pct
        FROM ml_features_materialized
    ''')
    ohlc_result = cursor.fetchone()
    print(f'OHLC Population: {ohlc_result[1]:,} / {ohlc_result[0]:,} ({ohlc_result[3]}%)')

    # Check macro indicators
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as dxy_pop,
            SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) as vix_pop,
            SUM(CASE WHEN spx IS NOT NULL THEN 1 ELSE 0 END) as spx_pop
        FROM ml_features_materialized
    ''')
    macro_result = cursor.fetchone()
    print(f'Macro Indicators - DXY: {macro_result[0]:,}, VIX: {macro_result[1]:,}, SPX: {macro_result[2]:,}')

    # Latest updates by symbol
    cursor.execute('''
        SELECT symbol, MAX(timestamp) as latest, COUNT(*) as records
        FROM ml_features_materialized 
        GROUP BY symbol 
        ORDER BY latest DESC 
        LIMIT 10
    ''')
    latest_symbols = cursor.fetchall()
    print('\\nLatest updated symbols:')
    for row in latest_symbols:
        print(f'  {row[0]}: {row[1]} ({row[2]:,} records)')

    # Date range
    cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM ml_features_materialized')
    date_range = cursor.fetchone()
    print(f'\\nDate Range: {date_range[0]} to {date_range[1]}')

    conn.close()

if __name__ == "__main__":
    main()