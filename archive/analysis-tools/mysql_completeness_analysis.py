#!/usr/bin/env python3
"""
MySQL Historical Data Completeness Analysis
"""

import mysql.connector
from datetime import datetime, timedelta
import sys

# MySQL connection details from K8s config
MYSQL_HOST = '172.22.32.1'
MYSQL_PORT = 3306
MYSQL_USER = 'news_collector' 
MYSQL_PASSWORD = '99Rules!'
MYSQL_DATABASE = 'crypto_prices'

def analyze_completeness():
    print("🔍 HISTORICAL DATA COMPLETENESS ANALYSIS")
    print("=" * 60)
    
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        cur = conn.cursor()
        print("✅ Connected to MySQL database")
        print()
        
        # Basic table statistics
        print("📊 BASIC TABLE STATISTICS")
        print("-" * 40)
        
        cur.execute("SELECT COUNT(*) FROM technical_indicators")
        total_rows = cur.fetchone()[0]
        print(f"Total records: {total_rows:,}")
        
        # Date range analysis  
        print("\n🗓️  DATE RANGE ANALYSIS")
        print("-" * 40)
        
        cur.execute("""
            SELECT 
                MIN(timestamp_iso) as earliest_date,
                MAX(timestamp_iso) as latest_date,
                COUNT(DISTINCT DATE(timestamp_iso)) as unique_dates,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM technical_indicators 
            WHERE timestamp_iso IS NOT NULL
        """)
        
        earliest, latest, unique_dates, unique_symbols = cur.fetchone()
        
        if earliest and latest:
            print(f"Earliest record: {earliest}")
            print(f"Latest record: {latest}")
            print(f"Date span: {(latest - earliest).days} days")
            print(f"Unique dates: {unique_dates:,}")
            print(f"Unique symbols: {unique_symbols}")
            
            # Expected vs actual dates
            expected_days = (latest - earliest).days + 1
            coverage_pct = (unique_dates / expected_days) * 100 if expected_days > 0 else 0
            print(f"Date coverage: {coverage_pct:.1f}%")
        
        # Symbol distribution analysis
        print("\n🪙 SYMBOL DISTRIBUTION")
        print("-" * 40)
        
        cur.execute("""
            SELECT 
                symbol,
                COUNT(*) as record_count,
                MIN(timestamp_iso) as first_record,
                MAX(timestamp_iso) as last_record,
                COUNT(DISTINCT DATE(timestamp_iso)) as unique_dates
            FROM technical_indicators 
            WHERE symbol IS NOT NULL AND timestamp_iso IS NOT NULL
            GROUP BY symbol
            ORDER BY record_count DESC
            LIMIT 15
        """)
        
        symbol_data = cur.fetchall()
        
        print(f"{'Symbol':<10} {'Records':<12} {'Days':<8} {'First Record':<12} {'Last Record'}")
        print("-" * 70)
        
        for symbol, count, first, last, days in symbol_data:
            first_str = first.strftime('%Y-%m-%d') if first else 'N/A'
            last_str = last.strftime('%Y-%m-%d') if last else 'N/A'
            print(f"{symbol:<10} {count:<12,} {days:<8} {first_str:<12} {last_str}")
        
        # Recent data quality check (last 30 days)
        print(f"\n📅 RECENT DATA QUALITY (Last 30 Days)")
        print("-" * 40)
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        cur.execute("""
            SELECT 
                DATE(timestamp_iso) as date,
                COUNT(*) as record_count,
                COUNT(DISTINCT symbol) as symbol_count
            FROM technical_indicators 
            WHERE timestamp_iso >= %s
            GROUP BY DATE(timestamp_iso)
            ORDER BY date DESC
            LIMIT 10
        """, (thirty_days_ago,))
        
        recent_data = cur.fetchall()
        
        if recent_data:
            print(f"{'Date':<12} {'Records':<10} {'Symbols'}")
            print("-" * 35)
            for date, records, symbols in recent_data:
                print(f"{date} {records:<10,} {symbols}")
        else:
            print("⚠️  No recent data found (last 30 days)")
        
        # Technical indicator completeness
        print(f"\n📈 TECHNICAL INDICATOR COMPLETENESS")
        print("-" * 40)
        
        # Key technical indicators to check
        key_indicators = [
            'sma_20', 'sma_50', 'sma_200', 
            'ema_12', 'ema_26',
            'rsi', 'rsi_14',
            'macd', 'macd_signal', 'macd_histogram',
            'bollinger_upper', 'bollinger_lower', 'bollinger_middle',
            'atr', 'adx'
        ]
        
        for indicator in key_indicators:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({indicator}) as non_null,
                    (COUNT({indicator}) * 100.0 / COUNT(*)) as completeness_pct
                FROM technical_indicators
                WHERE timestamp_iso IS NOT NULL
            """)
            
            total, non_null, completeness = cur.fetchone()
            if completeness is not None:
                print(f"{indicator:<20}: {non_null:>8,}/{total:,} ({completeness:>5.1f}%)")
        
        print()
        print("✅ Historical completeness analysis complete!")
        
        cur.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    analyze_completeness()
