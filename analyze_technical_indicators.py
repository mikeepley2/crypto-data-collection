#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import requests
import json

def main():
    print("=== TECHNICAL INDICATORS GENERATION ANALYSIS ===\n")
    
    try:
        connection = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # Check technical_indicators table status
        print("🔍 Analyzing technical_indicators table...")
        cursor.execute("DESCRIBE technical_indicators")
        columns = [col[0] for col in cursor.fetchall()]
        print(f"   Columns ({len(columns)}): {columns}")
        
        # Check data volume and freshness
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(timestamp) as earliest_timestamp,
                MAX(timestamp) as latest_timestamp,
                COUNT(CASE WHEN timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h,
                COUNT(CASE WHEN timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h
            FROM technical_indicators
        """)
        
        result = cursor.fetchone()
        if result:
            total, unique_symbols, earliest, latest, recent_24h, recent_1h = result
            print(f"   Total records: {total:,}")
            print(f"   Unique symbols: {unique_symbols}")
            print(f"   Timeframe: {earliest} to {latest}")
            print(f"   Recent 24h: {recent_24h:,}")
            print(f"   Recent 1h: {recent_1h:,}")
            
            # Check how fresh the data is
            if latest:
                time_since_latest = datetime.now() - latest
                print(f"   Data freshness: {time_since_latest} ago")
        
        # Check what technical indicators we have for key symbols
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as record_count,
                MAX(timestamp) as latest_update,
                AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as rsi_fill_rate,
                AVG(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as sma_fill_rate,
                AVG(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) as macd_fill_rate
            FROM technical_indicators
            WHERE symbol IN ('BTC', 'ETH', 'SOL', 'ADA', 'MATIC')
            GROUP BY symbol
            ORDER BY record_count DESC
        """)
        
        tech_data = cursor.fetchall()
        print(f"\n📊 TECHNICAL INDICATORS BY SYMBOL:")
        for symbol, count, latest_update, rsi_rate, sma_rate, macd_rate in tech_data:
            print(f"   {symbol}: {count:,} records, latest: {latest_update}")
            print(f"      RSI fill: {rsi_rate*100:.1f}%, SMA fill: {sma_rate*100:.1f}%, MACD fill: {macd_rate*100:.1f}%")
        
        # Check current ml_features_materialized technical field population
        print(f"\n🔍 Current technical field population in ml_features_materialized...")
        
        cursor.execute("DESCRIBE ml_features_materialized")
        all_columns = [col[0] for col in cursor.fetchall()]
        
        # Identify technical indicator fields
        tech_fields = [col for col in all_columns if any(indicator in col.lower() for indicator in 
                      ['rsi', 'sma', 'ema', 'macd', 'bb_', 'stoch', 'atr', 'vwap', 'adx', 'cci', 'williams'])]
        
        print(f"   Found {len(tech_fields)} technical fields: {tech_fields}")
        
        # Check population of technical fields
        if tech_fields:
            field_checks = []
            for field in tech_fields[:10]:  # Check first 10 to avoid query complexity
                field_checks.append(f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count")
            
            query = f"""
                SELECT 
                    COUNT(*) as total_symbols,
                    {', '.join(field_checks)}
                FROM ml_features_materialized
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total_symbols = result[0]
                print(f"\n📊 TECHNICAL FIELD POPULATION (out of {total_symbols} symbols):")
                
                populated_fields = 0
                for i, field in enumerate(tech_fields[:10]):
                    count = result[i + 1]
                    percentage = count / total_symbols * 100 if total_symbols > 0 else 0
                    status = "✅" if count > 0 else "❌"
                    print(f"   {status} {field}: {count} ({percentage:.1f}%)")
                    if count > 0:
                        populated_fields += 1
                
                print(f"\n🎯 TECHNICAL INDICATORS CATEGORY STATUS:")
                print(f"   Fields populated: {populated_fields}/{len(tech_fields[:10])}")
                print(f"   Category completion: {populated_fields/len(tech_fields[:10])*100:.1f}%")
        
        # Sample BTC technical values
        if tech_fields:
            cursor.execute(f"""
                SELECT {', '.join(tech_fields[:8])} 
                FROM ml_features_materialized 
                WHERE symbol = 'BTC'
            """)
            
            btc_result = cursor.fetchone()
            if btc_result:
                print(f"\n📋 BTC SAMPLE TECHNICAL VALUES:")
                for i, field in enumerate(tech_fields[:8]):
                    value = btc_result[i] if i < len(btc_result) else None
                    print(f"   {field}: {value}")
        
        cursor.close()
        connection.close()
        
        print(f"\n🔧 NEXT STEPS FOR TECHNICAL INDICATORS GENERATION:")
        print(f"   1. Check technical indicators service status")
        print(f"   2. Trigger fresh data generation")
        print(f"   3. Verify integration into ml_features_materialized")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()