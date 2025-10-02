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

    print('=== ML FEATURES OHLC POPULATION STATUS ===')

    # Check OHLC population in ml_features_materialized
    cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) as open_populated,
        SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) as close_populated,
        SUM(CASE WHEN volume IS NOT NULL THEN 1 ELSE 0 END) as volume_populated,
        ROUND(SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as open_percentage,
        ROUND(SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as close_percentage,
        ROUND(SUM(CASE WHEN volume IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as volume_percentage
    FROM ml_features_materialized
    WHERE symbol IN (SELECT DISTINCT symbol FROM ohlc_data)
    """)
    result = cursor.fetchone()
    total, open_pop, close_pop, vol_pop, open_pct, close_pct, vol_pct = result
    print(f'Total ML records for OHLC symbols: {total:,}')
    print(f'Open Price populated: {open_pop:,} ({open_pct}%)')
    print(f'Close Price populated: {close_pop:,} ({close_pct}%)')
    print(f'Volume populated: {vol_pop:,} ({vol_pct}%)')
    print()

    # Check recent data (last 7 days)
    cursor.execute("""
    SELECT 
        COUNT(*) as recent_total,
        SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) as recent_open,
        SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) as recent_close,
        ROUND(SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as recent_open_pct,
        ROUND(SUM(CASE WHEN close_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as recent_close_pct
    FROM ml_features_materialized 
    WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    AND symbol IN (SELECT DISTINCT symbol FROM ohlc_data)
    """)
    recent_result = cursor.fetchone()
    print(f'Last 7 days - Total: {recent_result[0]:,}')
    print(f'Last 7 days - Open: {recent_result[1]:,} ({recent_result[3]}%)')
    print(f'Last 7 days - Close: {recent_result[2]:,} ({recent_result[4]}%)')
    print()

    # Check materialized updater service status
    cursor.execute("SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
    recent_updates = cursor.fetchone()[0]
    print(f'Records updated in last hour: {recent_updates:,}')

    conn.close()

if __name__ == "__main__":
    main()