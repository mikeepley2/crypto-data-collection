#!/usr/bin/env python3
"""
Enhanced data population fixes for materialized updater
"""
import mysql.connector
import requests
import json
from datetime import datetime, timedelta

def add_data_population_enhancements():
    """
    Add enhancements to populate missing columns through:
    1. Technical indicators calculation/service calls
    2. Macro data interpolation for missing periods  
    3. Default values for social/sentiment when unavailable
    4. OHLC data fallback to price data when missing
    """
    
    print("=== IMPLEMENTING DATA POPULATION ENHANCEMENTS ===")
    
    # 1. Check technical indicators service endpoint
    try:
        response = requests.get("http://technical-indicators.crypto-collectors.svc.cluster.local:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Technical indicators service is accessible")
            
            # Test calculation endpoint
            test_payload = {
                "symbol": "BTC",
                "period": "14",
                "indicator": "rsi"
            }
            tech_response = requests.post(
                "http://technical-indicators.crypto-collectors.svc.cluster.local:8080/calculate",
                json=test_payload,
                timeout=10
            )
            if tech_response.status_code == 200:
                print("✅ Technical indicators calculation works")
            else:
                print(f"❌ Technical indicators calculation failed: {tech_response.status_code}")
        else:
            print(f"❌ Technical indicators service not responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Technical indicators service unreachable: {e}")
    
    # 2. Check macro data interpolation needs
    config = {
        'host': 'host.docker.internal',
        'user': 'news_collector', 
        'password': '99Rules!',
        'database': 'crypto_prices'
    }
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # Check macro indicators availability patterns
    cursor.execute("""
        SELECT indicator_name, COUNT(*) as count, MIN(indicator_date) as earliest, MAX(indicator_date) as latest
        FROM macro_indicators 
        GROUP BY indicator_name 
        ORDER BY count DESC
        LIMIT 10
    """)
    macro_availability = cursor.fetchall()
    
    print("\n📊 MACRO DATA AVAILABILITY:")
    for indicator, count, earliest, latest in macro_availability:
        print(f"  {indicator}: {count} records from {earliest} to {latest}")
    
    # 3. Implement solutions
    solutions = []
    
    # Solution 1: Technical indicators on-demand calculation
    solutions.append({
        "type": "technical_calculation",
        "description": "Calculate technical indicators on-demand when missing",
        "implementation": "Call technical service API or calculate inline using TA-lib"
    })
    
    # Solution 2: Macro data interpolation  
    solutions.append({
        "type": "macro_interpolation", 
        "description": "Interpolate macro indicators for missing time periods",
        "implementation": "Forward-fill latest values for daily/weekly indicators"
    })
    
    # Solution 3: Social data defaults
    solutions.append({
        "type": "social_defaults",
        "description": "Provide sensible defaults when social data unavailable", 
        "implementation": "Use 0 for counts, null for sentiment scores"
    })
    
    # Solution 4: OHLC fallback
    solutions.append({
        "type": "ohlc_fallback",
        "description": "Use price_data OHLC when ohlc_data missing",
        "implementation": "Map open/high/low/close from price_data table"
    })
    
    print("\n🔧 RECOMMENDED SOLUTIONS:")
    for i, solution in enumerate(solutions, 1):
        print(f"{i}. {solution['type']}: {solution['description']}")
        print(f"   Implementation: {solution['implementation']}")
    
    conn.close()
    return solutions

if __name__ == "__main__":
    add_data_population_enhancements()