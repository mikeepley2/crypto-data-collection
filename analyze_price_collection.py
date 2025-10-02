#!/usr/bin/env python3
"""
Price Collection Status Analysis
Comprehensive analysis of price collection status across all tables
"""

import mysql.connector
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'host': '192.168.230.162',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

def analyze_price_collection_status():
    """Analyze current price collection status across all tables"""
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    print("=== PRICE COLLECTION COMPREHENSIVE ANALYSIS ===")
    
    # Check price-related tables
    price_tables = [
        'price_data_real',
        'hourly_data', 
        'ohlc_data',
        'price_data'
    ]
    
    for table in price_tables:
        try:
            print(f"\n📊 Table: {table}")
            
            # Get basic stats
            cursor.execute(f"SELECT COUNT(*) as total_records FROM {table}")
            total = cursor.fetchone()['total_records']
            print(f"   Total records: {total:,}")
            
            if total > 0:
                # Get date range
                cursor.execute(f"""
                    SELECT 
                        MIN(timestamp_iso) as earliest,
                        MAX(timestamp_iso) as latest,
                        COUNT(DISTINCT symbol) as symbol_count
                    FROM {table}
                    WHERE timestamp_iso IS NOT NULL
                """)
                date_info = cursor.fetchone()
                
                if date_info['earliest']:
                    print(f"   Date range: {date_info['earliest']} to {date_info['latest']}")
                    print(f"   Symbols: {date_info['symbol_count']}")
                
                # Get recent activity (last 7 days)
                cursor.execute(f"""
                    SELECT COUNT(*) as recent_records
                    FROM {table}
                    WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
                """)
                recent = cursor.fetchone()['recent_records']
                print(f"   Recent (7 days): {recent:,} records ({recent/total*100:.1f}%)")
                
                # Check column completeness for key columns
                if table in ['price_data_real', 'hourly_data']:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = [row['Field'] for row in cursor.fetchall()]
                    
                    # Check key price columns
                    key_columns = ['current_price', 'volume_24h', 'market_cap', 'price_change_24h']
                    available_columns = [col for col in key_columns if col in columns]
                    
                    if available_columns:
                        print(f"   Key columns available: {available_columns}")
                        
                        for col in available_columns:
                            cursor.execute(f"""
                                SELECT 
                                    COUNT(CASE WHEN {col} IS NOT NULL THEN 1 END) as filled,
                                    COUNT(*) as total
                                FROM {table}
                                WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
                            """)
                            fill_info = cursor.fetchone()
                            if fill_info['total'] > 0:
                                fill_rate = fill_info['filled'] / fill_info['total'] * 100
                                print(f"      {col}: {fill_rate:.1f}% filled")
                
                # Get top symbols by volume
                cursor.execute(f"""
                    SELECT symbol, COUNT(*) as count
                    FROM {table}
                    WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
                    GROUP BY symbol
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_symbols = cursor.fetchall()
                if top_symbols:
                    symbol_list = [f"{s['symbol']}({s['count']})" for s in top_symbols[:5]]
                    print(f"   Top symbols (recent): {', '.join(symbol_list)}")
        
        except Exception as e:
            print(f"   ❌ Error analyzing {table}: {e}")
    
    # Check OHLC specific analysis
    print(f"\n📈 OHLC Data Analysis:")
    try:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT symbol) as ohlc_symbols,
                COUNT(*) as total_ohlc,
                MIN(timestamp_iso) as earliest_ohlc,
                MAX(timestamp_iso) as latest_ohlc
            FROM ohlc_data
        """)
        ohlc_stats = cursor.fetchone()
        
        print(f"   OHLC symbols: {ohlc_stats['ohlc_symbols']}")
        print(f"   OHLC records: {ohlc_stats['total_ohlc']:,}")
        print(f"   OHLC range: {ohlc_stats['earliest_ohlc']} to {ohlc_stats['latest_ohlc']}")
        
        # Check OHLC completeness
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN open_price IS NOT NULL THEN 1 END) as open_filled,
                COUNT(CASE WHEN high_price IS NOT NULL THEN 1 END) as high_filled,
                COUNT(CASE WHEN low_price IS NOT NULL THEN 1 END) as low_filled,
                COUNT(CASE WHEN close_price IS NOT NULL THEN 1 END) as close_filled,
                COUNT(CASE WHEN volume IS NOT NULL THEN 1 END) as volume_filled,
                COUNT(*) as total
            FROM ohlc_data
            WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
        """)
        ohlc_fill = cursor.fetchone()
        
        if ohlc_fill['total'] > 0:
            print(f"   OHLC completeness (recent 7 days):")
            print(f"      Open: {ohlc_fill['open_filled']/ohlc_fill['total']*100:.1f}%")
            print(f"      High: {ohlc_fill['high_filled']/ohlc_fill['total']*100:.1f}%")
            print(f"      Low: {ohlc_fill['low_filled']/ohlc_fill['total']*100:.1f}%")
            print(f"      Close: {ohlc_fill['close_filled']/ohlc_fill['total']*100:.1f}%")
            print(f"      Volume: {ohlc_fill['volume_filled']/ohlc_fill['total']*100:.1f}%")
        
    except Exception as e:
        print(f"   ❌ Error analyzing OHLC: {e}")
    
    # Check for data gaps
    print(f"\n🔍 Data Gap Analysis:")
    try:
        # Check for recent gaps in hourly_data 
        cursor.execute("""
            SELECT symbol, COUNT(*) as hourly_count
            FROM hourly_data 
            WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
            GROUP BY symbol
            HAVING hourly_count < 168  -- Less than 24*7 hours
            ORDER BY hourly_count ASC
            LIMIT 10
        """)
        gap_symbols = cursor.fetchall()
        
        if gap_symbols:
            print(f"   Symbols with potential hourly gaps:")
            for symbol in gap_symbols:
                print(f"      {symbol['symbol']}: {symbol['hourly_count']}/168 hours")
        else:
            print(f"   ✅ No significant hourly gaps detected")
            
    except Exception as e:
        print(f"   ❌ Error checking gaps: {e}")
    
    conn.close()
    print(f"\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    analyze_price_collection_status()