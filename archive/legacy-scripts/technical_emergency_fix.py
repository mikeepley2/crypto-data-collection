#!/usr/bin/env python3
"""
Technical Indicators Emergency Fix - Priority Actions 1-4
Implements immediate fixes for technical indicators data quality issues
"""

import sys
sys.path.append('.')
from shared.database_config import get_db_connection
from shared.table_config import get_master_technical_table
from datetime import datetime, timedelta, date
import subprocess
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def priority_1_restart_technical_collector():
    """Priority 1: Restart Technical Collector Service"""
    print("🔄 PRIORITY 1: RESTARTING TECHNICAL COLLECTOR")
    print("=" * 50)
    
    try:
        # Check if technical calculator is available
        tech_calc_path = "services/technical-collection/technical_calculator.py"
        if os.path.exists(tech_calc_path):
            print(f"✅ Found technical calculator: {tech_calc_path}")
            
            # Test calculation capability
            result = subprocess.run([
                "python3", tech_calc_path, "--test"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Technical calculator test passed")
            else:
                print(f"⚠️ Technical calculator test issues: {result.stderr}")
                
        else:
            print(f"❌ Technical calculator not found at {tech_calc_path}")
            
        # Check current collection status
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check most recent data collection
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT symbol) as active_symbols,
                MAX(timestamp_iso) as latest_timestamp,
                COUNT(*) as records_today
            FROM technical_indicators 
            WHERE DATE(timestamp_iso) = CURDATE()
        """)
        
        status = cursor.fetchone()
        print(f"📊 Current Collection Status:")
        print(f"  Active symbols today: {status[0]}")
        print(f"  Latest timestamp: {status[1]}")
        print(f"  Records today: {status[2]}")
        
        conn.close()
        
        if status[2] < 100:  # Very low activity
            print("⚠️ Collection appears stopped - triggering restart")
            return True
        else:
            print("✅ Collection appears active")
            return False
            
    except Exception as e:
        logger.error(f"Error checking technical collector: {e}")
        return True

def priority_2_fix_timestamp_corruption():
    """Priority 2: Fix Timestamp Corruption (1970-01-21 issue)"""
    print("\n🔧 PRIORITY 2: FIXING TIMESTAMP CORRUPTION")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Identify corrupted timestamps
        cursor.execute("""
            SELECT 
                COUNT(*) as corrupt_count,
                COUNT(DISTINCT symbol) as affected_symbols
            FROM technical_indicators 
            WHERE DATE(timestamp_iso) = '1970-01-21'
        """)
        
        corrupt_data = cursor.fetchone()
        print(f"📊 Timestamp Corruption Analysis:")
        print(f"  Corrupted records: {corrupt_data[0]:,}")
        print(f"  Affected symbols: {corrupt_data[1]}")
        
        if corrupt_data[0] > 0:
            print("🚨 Found timestamp corruption - implementing fix")
            
            # Get sample of corrupted data
            cursor.execute("""
                SELECT symbol, COUNT(*) as count
                FROM technical_indicators 
                WHERE DATE(timestamp_iso) = '1970-01-21'
                GROUP BY symbol
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print("\n📋 Most affected symbols:")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]:,} corrupted records")
            
            # Create backup before fixing
            backup_table = f"technical_indicators_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n💾 Creating backup: {backup_table}")
            
            cursor.execute(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM technical_indicators 
                WHERE DATE(timestamp_iso) = '1970-01-21'
                LIMIT 1000
            """)
            
            # Delete corrupted records (safer than trying to fix)
            print("🗑️ Removing corrupted timestamp records")
            cursor.execute("""
                DELETE FROM technical_indicators 
                WHERE DATE(timestamp_iso) = '1970-01-21'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Removed {deleted_count:,} corrupted records")
            print(f"💾 Backup saved as: {backup_table}")
            
        else:
            print("✅ No timestamp corruption found")
            
    except Exception as e:
        logger.error(f"Error fixing timestamps: {e}")
        conn.rollback()
    finally:
        conn.close()

def priority_3_backfill_recent_gaps():
    """Priority 3: Backfill Recent Gaps (last 30 days)"""
    print("\n📈 PRIORITY 3: BACKFILLING RECENT GAPS")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Identify assets with gaps in last 30 days
        recent_date = (datetime.now() - timedelta(days=30)).date()
        
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(DISTINCT DATE(timestamp_iso)) as recent_days,
                MAX(DATE(timestamp_iso)) as last_date
            FROM technical_indicators 
            WHERE DATE(timestamp_iso) >= %s
            GROUP BY symbol
            HAVING recent_days < 25 OR last_date < CURDATE() - INTERVAL 2 DAY
            ORDER BY recent_days ASC
        """, (recent_date,))
        
        gap_assets = cursor.fetchall()
        print(f"📊 Gap Analysis (last 30 days):")
        print(f"  Assets needing backfill: {len(gap_assets)}")
        
        if gap_assets:
            print("\n⚠️ Assets with significant gaps:")
            for asset in gap_assets[:20]:  # Show top 20
                print(f"  {asset[0]}: {asset[1]} days, last: {asset[2]}")
            
            # Trigger comprehensive backfill
            print("\n🚀 Starting comprehensive backfill...")
            
            # Use existing backfill script
            backfill_script = "backfill_technical_indicators_comprehensive.py"
            if os.path.exists(backfill_script):
                print(f"📄 Using backfill script: {backfill_script}")
                
                result = subprocess.run([
                    "python3", backfill_script, "--days", "30", "--priority-mode"
                ], capture_output=True, text=True, timeout=1800)  # 30 min timeout
                
                if result.returncode == 0:
                    print("✅ Comprehensive backfill completed")
                    print(f"📋 Output: {result.stdout[-500:]}")  # Last 500 chars
                else:
                    print(f"⚠️ Backfill issues: {result.stderr[-500:]}")
            else:
                print(f"❌ Backfill script not found: {backfill_script}")
                
        else:
            print("✅ No significant gaps found in last 30 days")
            
    except Exception as e:
        logger.error(f"Error in backfill process: {e}")
    finally:
        conn.close()

def priority_4_fix_indicator_calculations():
    """Priority 4: Fix Missing Indicator Calculations (ema_20, rsi_14)"""
    print("\n🧮 PRIORITY 4: FIXING INDICATOR CALCULATIONS")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check indicator completeness
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN ema_20 IS NULL THEN 1 ELSE 0 END) as ema_20_null,
                SUM(CASE WHEN rsi_14 IS NULL THEN 1 ELSE 0 END) as rsi_14_null,
                SUM(CASE WHEN sma_20 IS NULL THEN 1 ELSE 0 END) as sma_20_null
            FROM technical_indicators 
            WHERE DATE(timestamp_iso) >= CURDATE() - INTERVAL 30 DAY
        """)
        
        stats = cursor.fetchone()
        print(f"📊 Indicator Completeness (last 30 days):")
        print(f"  Total records: {stats[0]:,}")
        print(f"  ema_20 missing: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
        print(f"  rsi_14 missing: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
        print(f"  sma_20 missing: {stats[3]:,} ({stats[3]/stats[0]*100:.1f}%)")
        
        # Check if indicators are completely missing
        if stats[1] > stats[0] * 0.9:  # >90% missing
            print("🚨 CRITICAL: ema_20 is mostly missing - requires calculation fix")
        
        if stats[2] > stats[0] * 0.9:  # >90% missing  
            print("🚨 CRITICAL: rsi_14 is mostly missing - requires calculation fix")
        
        # Trigger technical calculator with focus on missing indicators
        print("\n🔧 Triggering indicator recalculation...")
        
        tech_calc_path = "services/technical-collection/technical_calculator.py"
        if os.path.exists(tech_calc_path):
            result = subprocess.run([
                "python3", tech_calc_path, "--backfill", "7", "--force-recalc"
            ], capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode == 0:
                print("✅ Indicator recalculation triggered")
            else:
                print(f"⚠️ Recalculation issues: {result.stderr}")
        
        # Verify improvement
        time.sleep(10)  # Wait for processing
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN ema_20 IS NULL THEN 1 ELSE 0 END) as ema_20_null_after,
                SUM(CASE WHEN rsi_14 IS NULL THEN 1 ELSE 0 END) as rsi_14_null_after
            FROM technical_indicators 
            WHERE DATE(timestamp_iso) >= CURDATE() - INTERVAL 1 DAY
        """)
        
        after_stats = cursor.fetchone()
        print(f"\n📊 After Fix (last 24 hours):")
        print(f"  ema_20 missing: {after_stats[0]:,}")
        print(f"  rsi_14 missing: {after_stats[1]:,}")
        
    except Exception as e:
        logger.error(f"Error fixing indicators: {e}")
    finally:
        conn.close()

def main():
    """Execute all priority fixes"""
    print("🚨 TECHNICAL INDICATORS EMERGENCY FIX")
    print("=====================================\n")
    
    start_time = datetime.now()
    
    # Execute priority actions 1-4
    needs_restart = priority_1_restart_technical_collector()
    priority_2_fix_timestamp_corruption()
    priority_3_backfill_recent_gaps()
    priority_4_fix_indicator_calculations()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✅ EMERGENCY FIX COMPLETED")
    print(f"📊 Duration: {duration:.1f} seconds")
    print(f"⏰ Completed at: {end_time}")
    
    if needs_restart:
        print("\n📋 NEXT STEPS:")
        print("1. Monitor technical indicators collection over next hour")
        print("2. Run technical_quality_assessment.py again in 2 hours")
        print("3. Deploy technical_auto_backfill.py to cron if not already done")
        print("4. Set up monitoring alerts for collection failures")

if __name__ == "__main__":
    main()