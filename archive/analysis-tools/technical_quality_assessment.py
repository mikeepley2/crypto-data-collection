#!/usr/bin/env python3
"""
Technical Indicators Data Quality Assessment
Check completeness, gaps, and implement auto-backfill for technical data
"""

import sys
sys.path.append('.')
from shared.database_config import get_db_connection
from shared.table_config import get_master_technical_table
from datetime import datetime, timedelta, date
import pandas as pd

def get_all_assets_from_config():
    """Get all assets that should have technical data"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if we have an assets table
    cursor.execute("SHOW TABLES LIKE 'assets'")
    if cursor.fetchone():
        cursor.execute("SELECT symbol FROM assets WHERE active = 1")
        assets = [row['symbol'] for row in cursor.fetchall()]
    else:
        # Fallback to getting from technical table
        tech_table = get_master_technical_table()
        cursor.execute(f"SELECT DISTINCT symbol FROM {tech_table}")
        assets = [row['symbol'] for row in cursor.fetchall()]
    
    conn.close()
    return sorted(assets)

def analyze_technical_data_quality():
    """Comprehensive analysis of technical indicators data quality"""
    print("🔍 TECHNICAL INDICATORS DATA QUALITY ASSESSMENT")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    tech_table = get_master_technical_table()
    
    # Get table structure
    print("📊 Technical Table Structure:")
    cursor.execute(f"DESCRIBE {tech_table}")
    columns = cursor.fetchall()
    indicator_columns = [col['Field'] for col in columns if col['Field'] not in ['id', 'symbol', 'timestamp_iso', 'timestamp', 'datetime_utc', 'updated_at']]
    print(f"  Table: {tech_table}")
    print(f"  Indicators: {len(indicator_columns)} columns")
    print(f"  Fields: {', '.join(indicator_columns[:10])}{'...' if len(indicator_columns) > 10 else ''}")
    
    # Get all assets that should have data
    all_assets = get_all_assets_from_config()
    print(f"\n🪙 Assets Analysis:")
    print(f"  Total assets configured: {len(all_assets)}")
    
    # Check which assets have technical data
    cursor.execute(f"SELECT DISTINCT symbol FROM {tech_table}")
    assets_with_tech_data = {row['symbol'] for row in cursor.fetchall()}
    
    missing_assets = set(all_assets) - assets_with_tech_data
    print(f"  Assets with technical data: {len(assets_with_tech_data)}")
    print(f"  Assets missing technical data: {len(missing_assets)}")
    if missing_assets:
        print(f"    Missing: {', '.join(sorted(list(missing_assets))[:10])}{'...' if len(missing_assets) > 10 else ''}")
    
    # Analyze date coverage for each asset
    print(f"\n📅 Date Coverage Analysis:")
    cursor.execute(f"""
        SELECT 
            symbol,
            MIN(DATE(timestamp_iso)) as first_date,
            MAX(DATE(timestamp_iso)) as last_date,
            COUNT(DISTINCT DATE(timestamp_iso)) as total_days,
            COUNT(*) as total_records
        FROM {tech_table}
        GROUP BY symbol
        ORDER BY total_days DESC
    """)
    
    coverage_data = cursor.fetchall()
    
    if coverage_data:
        # Calculate expected days (assuming we want last 2 years of data)
        target_start = datetime.now().date() - timedelta(days=730)  # 2 years
        today = datetime.now().date()
        expected_days = (today - target_start).days + 1
        
        print(f"  Expected days (last 2 years): {expected_days}")
        print(f"\n  Top 10 Assets by Coverage:")
        
        for i, asset in enumerate(coverage_data[:10], 1):
            completion = (asset['total_days'] / expected_days) * 100
            print(f"    {i:2d}. {asset['symbol']}: {asset['total_days']} days ({completion:.1f}% complete)")
            print(f"        Range: {asset['first_date']} to {asset['last_date']}")
        
        # Assets with poor coverage
        poor_coverage = [a for a in coverage_data if a['total_days'] < expected_days * 0.8]
        if poor_coverage:
            print(f"\n  ⚠️ Assets with <80% coverage ({len(poor_coverage)} assets):")
            for asset in poor_coverage[:10]:
                completion = (asset['total_days'] / expected_days) * 100
                print(f"    {asset['symbol']}: {completion:.1f}% ({asset['total_days']}/{expected_days} days)")
    
    # Check for data gaps in recent dates
    print(f"\n🔍 Recent Data Gaps Analysis:")
    recent_date = datetime.now().date() - timedelta(days=30)
    
    cursor.execute(f"""
        SELECT symbol, COUNT(DISTINCT DATE(timestamp_iso)) as recent_days
        FROM {tech_table}
        WHERE DATE(timestamp_iso) >= %s
        GROUP BY symbol
        HAVING recent_days < 25
        ORDER BY recent_days ASC
    """, (recent_date,))
    
    recent_gaps = cursor.fetchall()
    if recent_gaps:
        print(f"  Assets with gaps in last 30 days ({len(recent_gaps)} assets):")
        for asset in recent_gaps[:10]:
            print(f"    {asset['symbol']}: Only {asset['recent_days']} days in last 30")
    else:
        print(f"  ✅ No significant gaps in last 30 days")
    
    # Check data completeness for indicators
    print(f"\n📊 Indicator Completeness Analysis:")
    
    # Sample recent data to check for null values
    cursor.execute(f"""
        SELECT symbol, COUNT(*) as total_records
        FROM {tech_table}
        WHERE DATE(timestamp_iso) >= %s
        GROUP BY symbol
        ORDER BY total_records DESC
        LIMIT 5
    """, (recent_date,))
    
    sample_assets = cursor.fetchall()
    
    if sample_assets:
        for asset in sample_assets[:3]:  # Check top 3 assets
            symbol = asset['symbol']
            cursor.execute(f"""
                SELECT COUNT(*) as total_rows
                FROM {tech_table}
                WHERE symbol = %s AND DATE(timestamp_iso) >= %s
            """, (symbol, recent_date))
            
            total_rows = cursor.fetchone()['total_rows']
            
            if total_rows > 0:
                # Check null percentages for key indicators
                key_indicators = ['sma_20', 'ema_20', 'rsi_14', 'macd_line', 'bb_upper', 'bb_lower']
                available_indicators = [ind for ind in key_indicators if ind in indicator_columns]
                
                if available_indicators:
                    null_checks = []
                    for indicator in available_indicators[:5]:  # Check first 5
                        cursor.execute(f"""
                            SELECT 
                                COUNT(*) as total_rows,
                                COUNT({indicator}) as non_null_rows
                            FROM {tech_table}
                            WHERE symbol = %s AND DATE(timestamp_iso) >= %s
                        """, (symbol, recent_date))
                        
                        result = cursor.fetchone()
                        null_percentage = ((result['total_rows'] - result['non_null_rows']) / result['total_rows']) * 100
                        null_checks.append(f"{indicator}: {null_percentage:.1f}% null")
                    
                    print(f"    {symbol} (last 30 days): {', '.join(null_checks[:3])}")
    
    conn.close()
    return assets_with_tech_data, missing_assets, poor_coverage if 'poor_coverage' in locals() else []

def check_technical_gaps_for_asset(symbol, days_back=90):
    """Check for gaps in technical data for a specific asset"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    tech_table = get_master_technical_table()
    
    # Get existing dates
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    cursor.execute(f"""
        SELECT DISTINCT DATE(timestamp_iso) as date
        FROM {tech_table}
        WHERE symbol = %s 
        AND DATE(timestamp_iso) BETWEEN %s AND %s
        ORDER BY date
    """, (symbol, start_date, end_date))
    
    existing_dates = {row['date'] for row in cursor.fetchall()}
    
    # Generate expected dates (weekdays only for trading)
    expected_dates = []
    current_date = start_date
    while current_date <= end_date:
        # Include weekdays (Monday=0 to Friday=4)
        if current_date.weekday() < 5:
            expected_dates.append(current_date)
        current_date += timedelta(days=1)
    
    missing_dates = [d for d in expected_dates if d not in existing_dates]
    
    conn.close()
    return missing_dates, len(expected_dates), len(existing_dates)

def create_technical_auto_backfill_script():
    """Create a script for automatic technical indicators backfill"""
    backfill_script = '''#!/usr/bin/env python3
"""
Technical Indicators Auto-Backfill
Automatically detect and fill gaps in technical indicators data
"""

import sys
sys.path.append('.')
from shared.database_config import get_db_connection
from shared.table_config import get_master_technical_table
from datetime import datetime, timedelta
import subprocess
import os

def detect_and_backfill_gaps():
    """Detect gaps and trigger backfill"""
    print("🔍 AUTO-BACKFILL: Checking for technical indicator gaps")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    tech_table = get_master_technical_table()
    
    # Check recent data completeness
    recent_date = datetime.now().date() - timedelta(days=7)
    
    cursor.execute(f"""
        SELECT symbol, 
               COUNT(DISTINCT date) as recent_days,
               MAX(date) as last_date
        FROM {tech_table}
        WHERE DATE(timestamp_iso) >= %s
        GROUP BY symbol
        HAVING recent_days < 5 OR last_date < CURDATE() - INTERVAL 2 DAY
        ORDER BY recent_days ASC
    """, (recent_date,))
    
    assets_needing_backfill = cursor.fetchall()
    
    if assets_needing_backfill:
        print(f"⚠️ Found {len(assets_needing_backfill)} assets needing backfill:")
        for asset in assets_needing_backfill:
            print(f"  {asset['symbol']}: {asset['recent_days']} recent days, last: {asset['last_date']}")
        
        # Trigger technical indicators collector
        try:
            print("🚀 Starting technical indicators backfill...")
            result = subprocess.run([
                sys.executable, 
                "technical_indicators_collector.py", 
                "--backfill", 
                "--days", "30"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ Technical backfill completed successfully")
            else:
                print(f"❌ Technical backfill failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error running technical backfill: {e}")
    else:
        print("✅ No gaps detected - technical data is current")
    
    conn.close()

if __name__ == "__main__":
    detect_and_backfill_gaps()
'''
    
    with open('technical_auto_backfill.py', 'w') as f:
        f.write(backfill_script)
    
    print("📄 Created technical_auto_backfill.py")

def main():
    """Main analysis function"""
    # Run comprehensive analysis
    assets_with_data, missing_assets, poor_coverage = analyze_technical_data_quality()
    
    # Check gaps for major assets
    major_assets = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'LINK']
    print(f"\n🔍 DETAILED GAP ANALYSIS FOR MAJOR ASSETS:")
    
    for symbol in major_assets:
        if symbol in assets_with_data:
            missing_dates, expected, actual = check_technical_gaps_for_asset(symbol, 90)
            coverage_pct = (actual / expected) * 100 if expected > 0 else 0
            print(f"  {symbol}: {actual}/{expected} days ({coverage_pct:.1f}%), {len(missing_dates)} gaps")
            
            if missing_dates and len(missing_dates) <= 10:
                recent_gaps = [d.strftime('%Y-%m-%d') for d in missing_dates[-5:]]
                print(f"    Recent gaps: {', '.join(recent_gaps)}")
        else:
            print(f"  {symbol}: ❌ No technical data found")
    
    # Create auto-backfill script
    print(f"\n🔧 CREATING AUTO-BACKFILL INFRASTRUCTURE:")
    create_technical_auto_backfill_script()
    
    # Summary and recommendations
    print(f"\n📋 SUMMARY AND RECOMMENDATIONS:")
    
    if missing_assets:
        print(f"  ⚠️ {len(missing_assets)} assets have no technical data")
        print(f"  📝 Recommendation: Run initial technical collection for missing assets")
    
    if poor_coverage:
        print(f"  ⚠️ {len(poor_coverage)} assets have <80% data coverage")
        print(f"  📝 Recommendation: Run historical backfill for incomplete assets")
    
    print(f"  ✅ Auto-backfill script created: technical_auto_backfill.py")
    print(f"  📝 Recommendation: Run this script daily via cron to maintain data integrity")
    
    # Create a cron job suggestion
    print(f"\n⏰ SUGGESTED CRON JOB:")
    print(f"  # Run technical auto-backfill daily at 6 AM")
    print(f"  0 6 * * * cd /path/to/crypto-data-collection && python3 technical_auto_backfill.py")

if __name__ == "__main__":
    main()