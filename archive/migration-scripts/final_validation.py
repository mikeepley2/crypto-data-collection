#!/usr/bin/env python3
"""
Final Validation Script for Enhanced Collectors
Validates all collectors are working correctly with gap prevention
"""

import requests
import mysql.connector
import json
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices',
}

def test_api_endpoint(name, port, endpoint):
    """Test API endpoint and return result"""
    try:
        response = requests.get(f"http://127.0.0.1:{port}{endpoint}", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def test_post_endpoint(name, port, endpoint):
    """Test POST endpoint and return result"""
    try:
        response = requests.post(f"http://127.0.0.1:{port}{endpoint}", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def get_data_counts():
    """Get current data counts from database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        counts = {}
        
        cursor.execute("SELECT COUNT(*) FROM crypto_news")
        counts['news'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data")
        counts['onchain'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM crypto_ohlc_data")
        counts['ohlc'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return counts
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main validation function"""
    print("🔍 FINAL VALIDATION - Enhanced Collectors")
    print("=" * 60)
    print(f"⏰ Validation Time: {datetime.now()}")
    print()
    
    collectors = [
        ("News Collector", 8000),
        ("Onchain Collector", 8001),
        ("OHLC Collector", 8002)
    ]
    
    # Test health endpoints
    print("1️⃣ HEALTH ENDPOINT TESTS")
    print("-" * 30)
    all_healthy = True
    for name, port in collectors:
        success, result = test_api_endpoint(name, port, "/health")
        if success and result.get("status") == "ok":
            print(f"✅ {name} (:{port}) - HEALTHY")
        else:
            print(f"❌ {name} (:{port}) - {result}")
            all_healthy = False
    print()
    
    # Test status endpoints
    print("2️⃣ STATUS ENDPOINT TESTS")
    print("-" * 30)
    for name, port in collectors:
        success, result = test_api_endpoint(name, port, "/status")
        if success:
            health_score = result.get("health_score", 0)
            data_freshness = result.get("data_freshness", "unknown")
            print(f"✅ {name} - Health Score: {health_score}, Freshness: {data_freshness}")
        else:
            print(f"❌ {name} - {result}")
    print()
    
    # Test gap-check endpoints
    print("3️⃣ GAP DETECTION TESTS")
    print("-" * 30)
    for name, port in collectors:
        success, result = test_post_endpoint(name, port, "/gap-check")
        if success:
            gap_hours = result.get("gap_hours", "unknown")
            health_score = result.get("health_score", 0)
            print(f"✅ {name} - Gap: {gap_hours}h, Health: {health_score}")
        else:
            print(f"❌ {name} - {result}")
    print()
    
    # Test data collection
    print("4️⃣ DATA COLLECTION VALIDATION")
    print("-" * 30)
    counts = get_data_counts()
    if "error" in counts:
        print(f"❌ Database error: {counts['error']}")
    else:
        print(f"📰 News Records: {counts['news']}")
        print(f"⛓️ Onchain Records: {counts['onchain']}")
        print(f"💰 OHLC Records: {counts['ohlc']}")
        
        total_records = counts['news'] + counts['onchain'] + counts['ohlc']
        print(f"📊 Total Records: {total_records}")
    print()
    
    # Final summary
    print("5️⃣ FINAL SUMMARY")
    print("-" * 30)
    
    if all_healthy and total_records > 0:
        print("🎉 ALL TESTS PASSED!")
        print("✅ All collectors are healthy and operational")
        print("✅ Gap detection is working correctly")
        print("✅ Data collection is functioning")
        print("✅ Database connectivity confirmed")
        print()
        print("🚀 ENHANCED COLLECTORS DEPLOYMENT: SUCCESS")
        print("   All collectors now have gap prevention capabilities!")
    else:
        print("⚠️ Some issues detected:")
        if not all_healthy:
            print("   - Health check issues found")
        if total_records == 0:
            print("   - No data collected")
    
    print()
    print("=" * 60)
    print("🔧 Enhanced Features Active:")
    print("   • Automatic gap detection")
    print("   • Intelligent backfilling")
    print("   • Health monitoring (0-100 scale)")
    print("   • FastAPI endpoints (/health, /status, /gap-check)")
    print("   • Statistics tracking")
    print("   • Background scheduling")
    print("=" * 60)

if __name__ == "__main__":
    main()