#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime, timedelta
import mysql.connector

def main():
    print("=== TECHNICAL INDICATORS GENERATION IMPLEMENTATION ===\n")
    
    # Technical indicators service endpoint
    tech_service_url = "http://technical-indicators.crypto-collectors.svc.cluster.local:8000"
    
    # Key symbols to generate indicators for
    symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'MATIC', 'AVAX', 'DOT', 'LINK', 'UNI', 'ATOM']
    
    print(f"🔧 Forcing fresh technical indicators generation for {len(symbols)} symbols...")
    
    # Generate indicators for each symbol
    generated_count = 0
    for symbol in symbols:
        try:
            print(f"   📊 Processing {symbol}...")
            
            # Call the technical indicators service to generate fresh data
            response = requests.post(f"{tech_service_url}/calculate/{symbol}", 
                                   json={"force_recalculate": True, "days_back": 7},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ {symbol}: Generated {result.get('records_created', 0)} technical indicator records")
                generated_count += 1
                time.sleep(2)  # Rate limiting
            else:
                print(f"      ❌ {symbol}: HTTP {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"      ❌ {symbol}: Request failed - {e}")
        except Exception as e:
            print(f"      ❌ {symbol}: Error - {e}")
    
    print(f"\n🎯 Generated fresh indicators for {generated_count}/{len(symbols)} symbols")
    
    # Wait for data to be available
    print(f"\n⏳ Waiting 30 seconds for data to propagate...")
    time.sleep(30)
    
    # Verify the fresh data generation
    try:
        connection = mysql.connector.connect(
            host='host.docker.internal',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        
        cursor = connection.cursor()
        
        # Check for fresh technical indicators data
        cursor.execute("""
            SELECT 
                COUNT(*) as fresh_records,
                COUNT(DISTINCT symbol) as fresh_symbols,
                MAX(timestamp) as latest_timestamp
            FROM technical_indicators 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 2 HOUR)
        """)
        
        result = cursor.fetchone()
        if result:
            fresh_records, fresh_symbols, latest_timestamp = result
            print(f"📊 FRESH TECHNICAL INDICATORS:")
            print(f"   New records: {fresh_records:,}")
            print(f"   Symbols updated: {fresh_symbols}")
            print(f"   Latest timestamp: {latest_timestamp}")
        
        # Check specific symbols' latest indicators
        cursor.execute("""
            SELECT 
                symbol,
                MAX(timestamp) as latest_update,
                COUNT(*) as record_count
            FROM technical_indicators 
            WHERE symbol IN ('BTC', 'ETH', 'SOL') 
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
            GROUP BY symbol
            ORDER BY latest_update DESC
        """)
        
        results = cursor.fetchall()
        print(f"\n📋 SYMBOL-SPECIFIC UPDATES:")
        for symbol, latest_update, count in results:
            print(f"   {symbol}: {count} records, latest: {latest_update}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Database verification error: {e}")
    
    print(f"\n🚀 TECHNICAL INDICATORS GENERATION RESULTS:")
    print(f"   Service calls completed: {generated_count}/{len(symbols)}")
    print(f"   Fresh data generated: Ready for integration")
    print(f"   Next step: Materialized updater will integrate new indicators")

if __name__ == "__main__":
    main()