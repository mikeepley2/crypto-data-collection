#!/usr/bin/env python3
"""
📊 STRATEGIC ONCHAIN DATA BACKFILL PLAN
=====================================
Reality Check: We have 113,268 missing days across 110 assets (Jan 2023 - Nov 2025)
That's roughly 1,030 missing days per asset over ~1,038 total days.

STRATEGIC APPROACH:
1. Focus on recent data first (last 90 days) - most valuable for trading
2. Prioritize top market cap assets
3. Use efficient batch processing
4. Respect CoinGecko rate limits
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.table_config import get_master_onchain_table
from shared.database_config import get_db_connection, test_db_connection

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StrategicOnchainBackfill:
    """Strategic approach to onchain data backfill"""
    
    def __init__(self):
        """Initialize strategic backfill"""
        if not test_db_connection():
            raise ConnectionError("Database connection failed")
        
        self.onchain_table = get_master_onchain_table()
        logger.info(f"✅ Using table: {self.onchain_table}")
    
    def analyze_current_situation(self):
        """Analyze the current data situation"""
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Current data overview
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_assets,
                    MIN(DATE(timestamp)) as earliest_date,
                    MAX(DATE(timestamp)) as latest_date,
                    COUNT(DISTINCT DATE(timestamp)) as unique_days
                FROM {self.onchain_table}
            """)
            overview = cursor.fetchone()
            
            # Days since 2023
            days_since_2023 = (datetime.now() - datetime(2023, 1, 1)).days
            expected_total_records = overview['unique_assets'] * days_since_2023
            missing_records = expected_total_records - overview['total_records']
            
            print("\n" + "=" * 60)
            print("📊 ONCHAIN DATA SITUATION ANALYSIS")
            print("=" * 60)
            print(f"📈 Current Records: {overview['total_records']:,}")
            print(f"🎯 Assets: {overview['unique_assets']}")
            print(f"📅 Date Range: {overview['earliest_date']} to {overview['latest_date']}")
            print(f"📊 Unique Days: {overview['unique_days']}")
            print(f"⏱️ Days Since 2023: {days_since_2023}")
            print(f"🎯 Expected Records (if complete): {expected_total_records:,}")
            print(f"❌ Missing Records: {missing_records:,}")
            print(f"📊 Coverage: {(overview['total_records']/expected_total_records)*100:.1f}%")
            
            # Recent coverage analysis (last 90 days)
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as recent_records,
                    COUNT(DISTINCT symbol) as recent_assets,
                    COUNT(DISTINCT DATE(timestamp)) as recent_days
                FROM {self.onchain_table}
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            """)
            recent = cursor.fetchone()
            
            expected_recent = overview['unique_assets'] * 90
            recent_coverage = (recent['recent_records'] / expected_recent) * 100
            
            print(f"\n🕐 RECENT DATA (Last 90 Days):")
            print(f"📈 Records: {recent['recent_records']:,}")
            print(f"🎯 Assets: {recent['recent_assets']}")
            print(f"📅 Days: {recent['recent_days']}")
            print(f"🎯 Expected: {expected_recent:,}")
            print(f"📊 Recent Coverage: {recent_coverage:.1f}%")
            
            return {
                'overview': overview,
                'recent': recent,
                'missing_records': missing_records,
                'days_since_2023': days_since_2023,
                'recent_coverage': recent_coverage
            }
            
        finally:
            connection.close()
    
    def get_backfill_priorities(self):
        """Identify backfill priorities"""
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Assets with least recent coverage
            cursor.execute(f"""
                SELECT 
                    symbol,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                          THEN 1 END) as last_30_days,
                    COUNT(CASE WHEN timestamp >= DATE_SUB(NOW(), INTERVAL 90 DAY) 
                          THEN 1 END) as last_90_days,
                    MAX(timestamp) as last_update
                FROM {self.onchain_table}
                GROUP BY symbol
                ORDER BY last_30_days ASC, last_90_days ASC
                LIMIT 20
            """)
            priorities = cursor.fetchall()
            
            print(f"\n🎯 TOP BACKFILL PRIORITIES (Least Recent Data):")
            print("-" * 60)
            for asset in priorities[:10]:
                print(f"{asset['symbol']:8s} | "
                      f"30d: {asset['last_30_days']:3d} | "
                      f"90d: {asset['last_90_days']:3d} | "
                      f"Last: {asset['last_update']}")
            
            return priorities
            
        finally:
            connection.close()
    
    def recommend_strategy(self, analysis: dict):
        """Recommend strategic approach"""
        print(f"\n🚀 RECOMMENDED BACKFILL STRATEGY")
        print("=" * 60)
        
        if analysis['recent_coverage'] < 50:
            print("🎯 PRIORITY 1: Recent Data Backfill (Last 30-90 days)")
            print("   • Focus on filling recent gaps first")
            print("   • Most valuable for current trading/analysis")
            print("   • Manageable scope: ~3,300-9,900 API calls")
            print()
        
        if analysis['overview']['unique_days'] < 100:
            print("🎯 PRIORITY 2: Extend Coverage to 6 Months")
            print("   • Gradually extend to 180 days of history")
            print("   • Provides good historical context")
            print("   • Scope: ~19,800 API calls")
            print()
        
        print("⚠️ REALISTIC CONSTRAINTS:")
        print(f"   • Total missing: {analysis['missing_records']:,} records")
        print("   • CoinGecko free tier: ~1,000 calls/month")
        print("   • Premium tier: ~10,000 calls/month")
        print("   • Full backfill would take: 11+ months (free) or 1+ months (premium)")
        print()
        
        print("💡 RECOMMENDED PHASES:")
        print("   📅 Phase 1: Last 30 days (high priority)")
        print("   📅 Phase 2: Last 90 days (medium priority)")
        print("   📅 Phase 3: Last 180 days (nice to have)")
        print("   📅 Phase 4: Full historical (long-term project)")


def main():
    """Main analysis function"""
    logger.info("🚀 Starting Strategic Onchain Backfill Analysis...")
    
    try:
        analyzer = StrategicOnchainBackfill()
        
        # Analyze current situation
        analysis = analyzer.analyze_current_situation()
        
        # Get priorities
        priorities = analyzer.get_backfill_priorities()
        
        # Recommend strategy
        analyzer.recommend_strategy(analysis)
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")


if __name__ == "__main__":
    main()