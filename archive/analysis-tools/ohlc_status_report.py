#!/usr/bin/env python3
"""
OHLC Data and Collector Status Report
Comprehensive analysis of OHLC data collection status and health
"""

import sys
sys.path.append('.')
from shared.database_config import get_db_connection
from datetime import datetime, timedelta
import os

def generate_ohlc_status_report():
    print("🔍 OHLC DATA AND COLLECTOR STATUS REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now()}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. OHLC Data Overview
    print(f"\n📊 OHLC DATA OVERVIEW:")
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT symbol) FROM ohlc_data")
    total_ohlc, ohlc_symbols = cursor.fetchone()
    print(f"  Total OHLC records: {total_ohlc:,}")
    print(f"  Symbols with OHLC data: {ohlc_symbols}")
    
    # 2. Data Freshness
    cursor.execute("SELECT MAX(timestamp_iso), MIN(timestamp_iso) FROM ohlc_data")
    latest, earliest = cursor.fetchone()
    print(f"  Date range: {earliest} to {latest}")
    
    if latest:
        age_hours = (datetime.now() - latest).total_seconds() / 3600
        print(f"  Latest data age: {age_hours:.1f} hours")
        
        if age_hours < 24:
            freshness = "CURRENT"
        elif age_hours < 72:
            freshness = "RECENT"
        else:
            freshness = "STALE"
        print(f"  Data freshness: {freshness}")
    
    # 3. Top Assets by Coverage
    print(f"\n📈 TOP 15 ASSETS BY OHLC COVERAGE:")
    cursor.execute("""
        SELECT 
            symbol,
            COUNT(*) as total_records,
            MIN(DATE(timestamp_iso)) as earliest_date,
            MAX(DATE(timestamp_iso)) as latest_date,
            COUNT(DISTINCT DATE(timestamp_iso)) as unique_days
        FROM ohlc_data
        GROUP BY symbol
        ORDER BY total_records DESC
        LIMIT 15
    """)
    
    top_assets = cursor.fetchall()
    for symbol, records, earliest, latest, days in top_assets:
        if earliest and latest:
            expected_days = (latest - earliest).days + 1
            coverage = (days / expected_days * 100) if expected_days > 0 else 0
            print(f"  {symbol:6s}: {records:,} records | {days:,} days ({coverage:.1f}% coverage)")
    
    # 4. Recent Collection Activity
    print(f"\n⏰ RECENT COLLECTION ACTIVITY (last 7 days):")
    cursor.execute("""
        SELECT 
            DATE(timestamp_iso) as data_date,
            COUNT(*) as records,
            COUNT(DISTINCT symbol) as symbols
        FROM ohlc_data 
        WHERE timestamp_iso >= CURDATE() - INTERVAL 7 DAY
        GROUP BY DATE(timestamp_iso)
        ORDER BY data_date DESC
    """)
    
    recent_activity = cursor.fetchall()
    if recent_activity:
        for date, records, symbols in recent_activity:
            print(f"  {date}: {records:,} records across {symbols} symbols")
    else:
        print("  No recent OHLC collection activity detected")
    
    # 5. Collector Infrastructure Status
    print(f"\n🛠️ COLLECTOR INFRASTRUCTURE:")
    
    # Check collector script
    ohlc_script = "scripts/data-collection/comprehensive_ohlc_collector.py"
    if os.path.exists(ohlc_script):
        stat = os.stat(ohlc_script)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        print(f"  OHLC collector script: EXISTS ({stat.st_size:,} bytes)")
        print(f"  Last modified: {mod_time}")
    else:
        print(f"  OHLC collector script: MISSING")
    
    # 6. Data Quality Assessment
    print(f"\n🔍 DATA QUALITY ASSESSMENT:")
    
    # Check for gaps in major assets
    major_assets = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK']
    
    for asset in major_assets:
        cursor.execute("""
            SELECT 
                COUNT(*) as records,
                MIN(DATE(timestamp_iso)) as first_date,
                MAX(DATE(timestamp_iso)) as last_date,
                COUNT(DISTINCT DATE(timestamp_iso)) as unique_days
            FROM ohlc_data
            WHERE symbol = %s
        """, (asset,))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            records, first_date, last_date, days = result
            expected = (last_date - first_date).days + 1 if first_date and last_date else 0
            completeness = (days / expected * 100) if expected > 0 else 0
            
            if completeness > 90:
                status = "EXCELLENT"
            elif completeness > 70:
                status = "GOOD"
            elif completeness > 50:
                status = "FAIR"
            else:
                status = "POOR"
                
            print(f"  {asset}: {records:,} records, {completeness:.1f}% complete - {status}")
        else:
            print(f"  {asset}: NO DATA")
    
    # 7. Comparison with Other Data Sources
    print(f"\n🔄 DATA SOURCE COMPARISON:")
    
    # Technical indicators
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT symbol) FROM technical_indicators")
    tech_total, tech_symbols = cursor.fetchone()
    print(f"  Technical indicators: {tech_total:,} records, {tech_symbols} symbols")
    
    # ML features
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT symbol) FROM ml_features_materialized")
    ml_total, ml_symbols = cursor.fetchone()
    print(f"  ML features: {ml_total:,} records, {ml_symbols} symbols")
    
    # Coverage analysis
    print(f"\n📊 COVERAGE ANALYSIS:")
    print(f"  OHLC coverage: {ohlc_symbols} symbols")
    print(f"  Technical coverage: {tech_symbols} symbols")
    print(f"  ML features coverage: {ml_symbols} symbols")
    
    ohlc_tech_ratio = (ohlc_symbols / tech_symbols * 100) if tech_symbols > 0 else 0
    print(f"  OHLC vs Technical: {ohlc_tech_ratio:.1f}%")
    
    # 8. Collection Performance Metrics
    print(f"\n⚡ PERFORMANCE METRICS:")
    
    if total_ohlc > 0:
        # Calculate records per symbol
        avg_records_per_symbol = total_ohlc / ohlc_symbols
        print(f"  Average records per symbol: {avg_records_per_symbol:.0f}")
        
        # Estimate collection efficiency
        if total_ohlc > 500000:
            efficiency = "HIGH"
        elif total_ohlc > 100000:
            efficiency = "MEDIUM"
        else:
            efficiency = "LOW"
        print(f"  Collection efficiency: {efficiency}")
    
    # 9. Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not recent_activity:
        print("  ⚠️ No recent OHLC collection - consider running comprehensive_ohlc_collector.py")
    
    if ohlc_tech_ratio < 95:
        print("  📈 OHLC coverage below technical indicators - run backfill for missing symbols")
    
    if age_hours > 48:
        print("  🔄 Data is getting stale - schedule regular OHLC collection")
    
    if total_ohlc < 500000:
        print("  📊 Consider comprehensive historical OHLC backfill")
    
    # 10. Overall Health Score
    health_score = 100
    
    if not recent_activity:
        health_score -= 30
    if age_hours > 48:
        health_score -= 20
    if ohlc_tech_ratio < 90:
        health_score -= 20
    if total_ohlc < 100000:
        health_score -= 30
    
    health_score = max(0, health_score)
    
    if health_score >= 80:
        health_status = "EXCELLENT"
    elif health_score >= 60:
        health_status = "GOOD"
    elif health_score >= 40:
        health_status = "FAIR"
    else:
        health_status = "POOR"
    
    print(f"\n🎯 OVERALL HEALTH ASSESSMENT:")
    print(f"  Health Score: {health_score}/100")
    print(f"  Status: {health_status}")
    
    conn.close()
    print(f"\nReport completed at {datetime.now()}")

if __name__ == "__main__":
    generate_ohlc_status_report()