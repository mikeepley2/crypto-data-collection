#!/usr/bin/env python3
"""
Enhanced Macro Collector Monitoring Script
- Monitors the status of all 11 macro indicators
- Provides real-time health assessment
- Alerts for any gaps or issues
- Can be run periodically to ensure continuous operation
"""

import mysql.connector
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MacroCollectorMonitor:
    """Monitor for enhanced macro collector"""
    
    def __init__(self):
        self.db_config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices',
        }
        
        # All 11 key indicators being monitored
        self.monitored_indicators = {
            'VIX': {'frequency': 'daily', 'priority': 'high'},
            'DXY': {'frequency': 'daily', 'priority': 'high'},
            'OIL_PRICE': {'frequency': 'daily', 'priority': 'high'},
            'US_GDP': {'frequency': 'quarterly', 'priority': 'medium'},
            'US_INFLATION': {'frequency': 'monthly', 'priority': 'high'},
            'US_UNEMPLOYMENT': {'frequency': 'monthly', 'priority': 'high'},
            'GOLD_PRICE': {'frequency': 'daily', 'priority': 'medium'},
            'US_10Y_YIELD': {'frequency': 'daily', 'priority': 'high'},
            'DGS10': {'frequency': 'daily', 'priority': 'high'},
            'DGS2': {'frequency': 'daily', 'priority': 'high'},
            'FEDFUNDS': {'frequency': 'monthly', 'priority': 'high'}
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_indicator_status(self, indicator_name):
        """Get comprehensive status for an indicator"""
        conn = self.get_db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    MAX(indicator_date) as last_date,
                    MIN(indicator_date) as first_date,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT indicator_date) as unique_dates
                FROM macro_indicators 
                WHERE indicator_name = %s
            """, (indicator_name,))
            
            result = cursor.fetchone()
            if not result or not result[0]:
                return None
            
            last_date, first_date, total_records, unique_dates = result
            
            # Get recent collection activity
            cursor.execute("""
                SELECT 
                    data_source,
                    COUNT(*) as count,
                    MAX(collected_at) as last_collected
                FROM macro_indicators 
                WHERE indicator_name = %s 
                AND indicator_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY data_source
                ORDER BY last_collected DESC
            """, (indicator_name,))
            
            recent_sources = cursor.fetchall()
            
            return {
                'last_date': last_date,
                'first_date': first_date,
                'total_records': total_records,
                'unique_dates': unique_dates,
                'recent_sources': recent_sources
            }
            
        except Exception as e:
            logger.error(f"Error getting status for {indicator_name}: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def check_collector_health(self):
        """Check overall health of the macro collector"""
        logger.info("🏥 ENHANCED MACRO COLLECTOR HEALTH CHECK")
        logger.info("=" * 60)
        
        today = datetime.now().date()
        health_summary = {
            'excellent': [],
            'good': [],
            'stale': [],
            'gaps': [],
            'missing': []
        }
        
        total_records = 0
        
        logger.info("\n📊 Individual Indicator Status:")
        
        for indicator_name, config in self.monitored_indicators.items():
            status_info = self.get_indicator_status(indicator_name)
            
            if not status_info:
                health_summary['missing'].append(indicator_name)
                logger.info(f"   ❌ MISSING   {indicator_name:18} No data found")
                continue
            
            last_date = status_info['last_date']
            total_records += status_info['total_records']
            days_behind = (today - last_date).days
            
            # Determine health status based on frequency and days behind
            if config['frequency'] == 'daily':
                if days_behind <= 1:
                    status = "✅ EXCELLENT"
                    health_summary['excellent'].append(indicator_name)
                elif days_behind <= 3:
                    status = "🟢 GOOD"
                    health_summary['good'].append(indicator_name)
                elif days_behind <= 7:
                    status = "⚠️ STALE"
                    health_summary['stale'].append(indicator_name)
                else:
                    status = "❌ GAP"
                    health_summary['gaps'].append(indicator_name)
            elif config['frequency'] == 'monthly':
                if days_behind <= 31:
                    status = "✅ EXCELLENT"
                    health_summary['excellent'].append(indicator_name)
                elif days_behind <= 35:
                    status = "🟢 GOOD"
                    health_summary['good'].append(indicator_name)
                elif days_behind <= 45:
                    status = "⚠️ STALE"
                    health_summary['stale'].append(indicator_name)
                else:
                    status = "❌ GAP"
                    health_summary['gaps'].append(indicator_name)
            else:  # quarterly
                if days_behind <= 93:
                    status = "✅ EXCELLENT"
                    health_summary['excellent'].append(indicator_name)
                elif days_behind <= 100:
                    status = "🟢 GOOD"
                    health_summary['good'].append(indicator_name)
                elif days_behind <= 120:
                    status = "⚠️ STALE"
                    health_summary['stale'].append(indicator_name)
                else:
                    status = "❌ GAP"
                    health_summary['gaps'].append(indicator_name)
            
            # Show recent collection sources
            recent_sources = status_info['recent_sources']
            main_source = recent_sources[0][0] if recent_sources else "unknown"
            
            logger.info(f"   {status:12} {indicator_name:18} "
                       f"Last: {last_date} ({days_behind} days ago) "
                       f"[{status_info['total_records']:,} records, source: {main_source}]")
        
        # Overall health summary
        total_indicators = len(self.monitored_indicators)
        excellent_count = len(health_summary['excellent'])
        good_count = len(health_summary['good'])
        stale_count = len(health_summary['stale'])
        gap_count = len(health_summary['gaps'])
        missing_count = len(health_summary['missing'])
        
        # Calculate health score
        health_score = (
            excellent_count * 100 +
            good_count * 85 +
            stale_count * 60 +
            gap_count * 20 +
            missing_count * 0
        ) / total_indicators
        
        logger.info(f"\n🎯 HEALTH SUMMARY:")
        logger.info(f"   ✅ Excellent: {excellent_count:2}/{total_indicators} ({(excellent_count/total_indicators)*100:.1f}%)")
        logger.info(f"   🟢 Good:      {good_count:2}/{total_indicators} ({(good_count/total_indicators)*100:.1f}%)")
        logger.info(f"   ⚠️ Stale:     {stale_count:2}/{total_indicators} ({(stale_count/total_indicators)*100:.1f}%)")
        logger.info(f"   ❌ Gaps:      {gap_count:2}/{total_indicators} ({(gap_count/total_indicators)*100:.1f}%)")
        logger.info(f"   🚫 Missing:   {missing_count:2}/{total_indicators} ({(missing_count/total_indicators)*100:.1f}%)")
        
        logger.info(f"\n🏆 OVERALL HEALTH SCORE: {health_score:.1f}/100")
        
        # Health status classification
        if health_score >= 95:
            health_status = "🟢 EXCELLENT"
        elif health_score >= 85:
            health_status = "🟡 GOOD"
        elif health_score >= 70:
            health_status = "🟠 FAIR"
        elif health_score >= 50:
            health_status = "🔴 POOR"
        else:
            health_status = "💀 CRITICAL"
        
        logger.info(f"🎯 STATUS: {health_status}")
        logger.info(f"📊 Total Records: {total_records:,}")
        
        # Recommendations
        if gap_count > 0 or missing_count > 0:
            logger.info(f"\n⚠️ RECOMMENDATIONS:")
            if gap_count > 0:
                logger.info(f"   🔄 Run manual backfill for gap indicators: {health_summary['gaps']}")
            if missing_count > 0:
                logger.info(f"   📊 Check collector configuration for missing indicators: {health_summary['missing']}")
            logger.info(f"   🔍 Verify enhanced macro collector is running: kubectl get pods -n crypto-data-collection -l app=enhanced-macro-collector")
        else:
            logger.info(f"\n🎉 ALL SYSTEMS HEALTHY - Enhanced macro collector is working perfectly!")
        
        return health_summary, health_score
    
    def check_collection_activity(self):
        """Check recent collection activity"""
        logger.info("\n📈 RECENT COLLECTION ACTIVITY (Last 7 days):")
        logger.info("-" * 60)
        
        conn = self.get_db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Get activity by data source
            cursor.execute("""
                SELECT 
                    data_source,
                    COUNT(*) as records,
                    COUNT(DISTINCT indicator_name) as indicators,
                    MIN(indicator_date) as first_date,
                    MAX(indicator_date) as last_date,
                    MAX(collected_at) as last_collection
                FROM macro_indicators 
                WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY data_source
                ORDER BY last_collection DESC
            """)
            
            activity = cursor.fetchall()
            
            if activity:
                for source, records, indicators, first_date, last_date, last_collection in activity:
                    logger.info(f"   📊 {source:30} {records:4} records, {indicators:2} indicators")
                    logger.info(f"      📅 Data range: {first_date} → {last_date}")
                    logger.info(f"      ⏰ Last collected: {last_collection}")
                    logger.info("")
            else:
                logger.info("   ⚠️ No recent collection activity found!")
                logger.info("   🔍 Check if enhanced macro collector is running")
            
        except Exception as e:
            logger.error(f"Error checking collection activity: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def run_full_monitoring(self):
        """Run complete monitoring check"""
        logger.info("🎯 ENHANCED MACRO COLLECTOR MONITORING")
        logger.info("=" * 80)
        logger.info(f"📅 Monitoring Time: {datetime.now()}")
        
        # Health check
        health_summary, health_score = self.check_collector_health()
        
        # Activity check
        self.check_collection_activity()
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("🎯 MONITORING COMPLETE")
        
        if health_score >= 85:
            logger.info("✅ Enhanced macro collector is operating excellently!")
        elif health_score >= 70:
            logger.info("🟡 Enhanced macro collector is operating well with minor issues")
        else:
            logger.info("🔴 Enhanced macro collector needs attention - check gaps and missing indicators")
        
        return health_summary, health_score


def main():
    """Main monitoring function"""
    monitor = MacroCollectorMonitor()
    health_summary, health_score = monitor.run_full_monitoring()
    
    # Return appropriate exit code for automation
    if health_score >= 70:
        exit(0)  # Success
    else:
        exit(1)  # Needs attention


if __name__ == "__main__":
    main()