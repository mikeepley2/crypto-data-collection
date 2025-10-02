#!/usr/bin/env python3
"""
Quick Collection Test - Focus on identifying the core issue
"""
import requests
import json
import time
import os
import pymysql
from datetime import datetime, timedelta

def test_database_from_host():
    """Test database connectivity from host machine"""
    print("\n🔍 TESTING DATABASE FROM HOST MACHINE:")
    print("-" * 40)
    
    try:
        # Test connection
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='rootpassword',
            database='crypto_prices',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Check recent data
            cursor.execute("""
                SELECT COUNT(*) as count, MAX(timestamp) as latest
                FROM crypto_prices 
                WHERE timestamp > %s
            """, (datetime.now() - timedelta(hours=1),))
            
            result = cursor.fetchone()
            print(f"✅ Database connection successful")
            print(f"📊 Records in last hour: {result[0]}")
            print(f"🕐 Latest timestamp: {result[1]}")
            
            # Check total records
            cursor.execute("SELECT COUNT(*) FROM crypto_prices")
            total = cursor.fetchone()[0]
            print(f"📈 Total records: {total}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_service_collection():
    """Test actual collection by triggering services"""
    print("\n🔍 TESTING SERVICE COLLECTION:")
    print("-" * 40)
    
    services = [
        ("enhanced-crypto-prices", 8001),
        ("crypto-news-collector", 8002),
        ("technical-indicators", 8004)
    ]
    
    for service, port in services:
        try:
            print(f"\n🎯 Testing {service}...")
            
            # Check health
            health_url = f"http://localhost:{port}/health"
            health_resp = requests.get(health_url, timeout=5)
            print(f"  Health: {health_resp.status_code}")
            
            # Try to trigger collection
            collect_url = f"http://localhost:{port}/collect"
            collect_resp = requests.post(collect_url, timeout=30)
            print(f"  Collection trigger: {collect_resp.status_code}")
            
            if collect_resp.status_code == 200:
                try:
                    result = collect_resp.json()
                    print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
                except:
                    print(f"  Response: {collect_resp.text[:200]}...")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")

def check_collector_manager_status():
    """Check what the collector manager thinks is happening"""
    print("\n🔍 COLLECTOR MANAGER STATUS:")
    print("-" * 40)
    
    try:
        # Get schedule status
        resp = requests.get("http://localhost:8010/schedule", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Total jobs: {data.get('total_jobs', 0)}")
            print(f"Enabled jobs: {data.get('enabled_jobs', 0)}")
            
            for job_id, job in data.get('jobs', {}).items():
                service = job.get('service_name', 'unknown')
                run_count = job.get('run_count', 0)
                error_count = job.get('error_count', 0)
                success_rate = job.get('success_rate', 0)
                last_run = job.get('last_run', 'never')
                
                print(f"\n  {service}:")
                print(f"    Runs: {run_count}, Errors: {error_count}")
                print(f"    Success rate: {success_rate:.1%}")
                print(f"    Last run: {last_run}")
                
    except Exception as e:
        print(f"❌ Failed to get collector manager status: {e}")

def main():
    print("🚀 QUICK COLLECTION DIAGNOSTIC")
    print("=" * 50)
    print("🎯 Focus: Identify why data isn't being collected")
    print()
    
    # Test database first
    db_ok = test_database_from_host()
    
    # Check collector manager
    check_collector_manager_status()
    
    # Test services
    test_service_collection()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    if db_ok:
        print("✅ Database is accessible from host")
        print("❓ Issue likely in service->database connection OR data writing logic")
    else:
        print("❌ Database connection failed - this could be the root cause")
    
    print("\n💡 NEXT STEPS:")
    print("1. Check if services can actually write to database")
    print("2. Verify database credentials in service configs")
    print("3. Check if there are database permission issues")

if __name__ == "__main__":
    main()