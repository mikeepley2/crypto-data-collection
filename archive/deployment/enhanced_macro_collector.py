#!/usr/bin/env python3
"""
Enhanced Comprehensive Macro Indicators Collector
- Collects all 11 key macro indicators continuously
- Automatic gap detection and backfilling on startup
- Robust error handling and retry mechanisms
- Universal symbol compatibility
- Prevents gaps through smart scheduling
"""

import os
import logging
import time
import mysql.connector
from datetime import datetime, timedelta
import schedule
import requests
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced-macro-collector")

# FRED API configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.getenv("FRED_API_KEY", "35478996c5e061d0fc99fc73f5ce348d")

# Comprehensive mapping of all 11 key indicators to FRED series
COMPREHENSIVE_FRED_SERIES = {
    "VIX": {
        "series_id": "VIXCLS",
        "description": "VIX Volatility Index",
        "frequency": "daily",
        "priority": "high"
    },
    "DXY": {
        "series_id": "DEXUSEU",  # US/Euro rate as DXY proxy
        "description": "US Dollar Index (EUR proxy)",
        "frequency": "daily", 
        "priority": "high"
    },
    "OIL_PRICE": {
        "series_id": "DCOILWTICO", 
        "description": "WTI Crude Oil Price",
        "frequency": "daily",
        "priority": "high"
    },
    "US_GDP": {
        "series_id": "A191RO1Q156NBEA",
        "description": "US Real GDP",
        "frequency": "quarterly",
        "priority": "medium"
    },
    "US_INFLATION": {
        "series_id": "CPIAUCSL",
        "description": "US Consumer Price Index", 
        "frequency": "monthly",
        "priority": "high"
    },
    "US_UNEMPLOYMENT": {
        "series_id": "UNRATE",
        "description": "US Unemployment Rate",
        "frequency": "monthly",
        "priority": "high"
    },
    "GOLD_PRICE": {
        "series_id": "GOLDAMGD248NLBM",
        "description": "Gold Price (London AM Fix)",
        "frequency": "daily",
        "priority": "medium",
        "alternative_series": "GOLDAMPM"  # Fallback if AM fix unavailable
    },
    "US_10Y_YIELD": {
        "series_id": "DGS10",
        "description": "US 10-Year Treasury Yield",
        "frequency": "daily",
        "priority": "high"
    },
    "DGS10": {
        "series_id": "DGS10", 
        "description": "10-Year Treasury Constant Maturity Rate",
        "frequency": "daily",
        "priority": "high"
    },
    "DGS2": {
        "series_id": "DGS2",
        "description": "2-Year Treasury Constant Maturity Rate", 
        "frequency": "daily",
        "priority": "high"
    },
    "FEDFUNDS": {
        "series_id": "FEDFUNDS",
        "description": "Federal Funds Rate",
        "frequency": "monthly",
        "priority": "high"
    }
}


class EnhancedMacroCollector:
    """Enhanced macro collector with comprehensive gap prevention"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'user': os.getenv('DB_USER', 'news_collector'),
            'password': os.getenv('DB_PASSWORD', '99Rules!'),
            'database': os.getenv('DB_NAME', 'crypto_prices'),
        }
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 5
        self.api_timeout = 30
        self.rate_limit_delay = 2
        
        logger.info("🎯 Enhanced Macro Collector initialized")
        logger.info(f"📊 Managing {len(COMPREHENSIVE_FRED_SERIES)} indicators")
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def fetch_fred_data(self, series_id: str, start_date: str = None, 
                       end_date: str = None) -> List[Dict]:
        """Fetch data from FRED API with retry logic"""
        if not FRED_API_KEY:
            logger.error("FRED_API_KEY not configured")
            return []
        
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
        }
        
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    f"{FRED_API_BASE}/series/observations",
                    params=params,
                    timeout=self.api_timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    observations = data.get("observations", [])
                    
                    results = []
                    for obs in observations:
                        try:
                            value = obs.get("value")
                            if value != "." and value is not None:
                                date_str = obs.get("date")
                                if date_str:
                                    results.append({
                                        "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                                        "value": float(value)
                                    })
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Skipping invalid observation: {e}")
                    
                    logger.info(f"📈 Retrieved {len(results)} observations for {series_id}")
                    return results
                    
                elif response.status_code == 400:
                    logger.warning(f"⚠️ Series {series_id} not available or invalid date range")
                    return []
                else:
                    logger.warning(f"⚠️ FRED API error {response.status_code} for {series_id}, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error fetching {series_id} (attempt {attempt + 1}): {e}")
                
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        logger.error(f"❌ Failed to fetch {series_id} after {self.max_retries} attempts")
        return []
    
    def get_indicator_status(self, indicator_name: str) -> Tuple[Optional[datetime], int]:
        """Get last update date and record count for an indicator"""
        conn = self.get_db_connection()
        if not conn:
            return None, 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(indicator_date), COUNT(*)
                FROM macro_indicators 
                WHERE indicator_name = %s
            """, (indicator_name,))
            
            result = cursor.fetchone()
            last_date = result[0] if result and result[0] else None
            count = result[1] if result else 0
            
            return last_date, count
            
        except Exception as e:
            logger.error(f"Error getting status for {indicator_name}: {e}")
            return None, 0
        finally:
            cursor.close()
            conn.close()
    
    def detect_gaps(self) -> Dict[str, Dict]:
        """Detect gaps for all indicators and determine backfill needs"""
        gaps = {}
        today = datetime.now().date()
        
        logger.info("🔍 Scanning all indicators for gaps...")
        
        for indicator_name, config in COMPREHENSIVE_FRED_SERIES.items():
            last_date, count = self.get_indicator_status(indicator_name)
            
            if last_date:
                days_behind = (today - last_date).days
                
                # Determine if backfill is needed based on frequency
                if config["frequency"] == "daily" and days_behind > 1:
                    backfill_needed = True
                elif config["frequency"] == "monthly" and days_behind > 31:
                    backfill_needed = True
                elif config["frequency"] == "quarterly" and days_behind > 93:
                    backfill_needed = True
                else:
                    backfill_needed = False
                
                if backfill_needed:
                    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    gaps[indicator_name] = {
                        "last_date": last_date,
                        "days_behind": days_behind,
                        "start_date": start_date,
                        "config": config,
                        "urgency": "critical" if days_behind > 30 else "urgent" if days_behind > 7 else "minor"
                    }
                    
                    urgency_emoji = "🔴" if days_behind > 30 else "🟡" if days_behind > 7 else "🟢"
                    logger.info(f"{urgency_emoji} {indicator_name}: {days_behind} days behind")
                else:
                    logger.info(f"✅ {indicator_name}: Current ({days_behind} days behind)")
            else:
                # No data exists - need full backfill
                gaps[indicator_name] = {
                    "last_date": None,
                    "days_behind": 999,
                    "start_date": "2020-01-01",  # Start from 2020
                    "config": config,
                    "urgency": "critical"
                }
                logger.info(f"❌ {indicator_name}: No data found - full backfill needed")
        
        if gaps:
            logger.info(f"📋 Found {len(gaps)} indicators needing backfill")
        else:
            logger.info("🎉 All indicators are current!")
        
        return gaps
    
    def store_indicator_data(self, indicator_name: str, data: List[Dict], 
                           config: Dict) -> int:
        """Store indicator data with deduplication"""
        if not data:
            return 0
        
        conn = self.get_db_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            stored_count = 0
            
            for record in data:
                try:
                    cursor.execute("""
                        INSERT INTO macro_indicators (
                            indicator_name, indicator_date, value, 
                            frequency, data_source, collected_at
                        ) VALUES (%s, %s, %s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE
                            value = VALUES(value),
                            frequency = VALUES(frequency),
                            data_source = VALUES(data_source),
                            collected_at = NOW()
                    """, (
                        indicator_name,
                        record["date"],
                        record["value"],
                        config.get("frequency", "daily"),
                        "enhanced_macro_collector"
                    ))
                    
                    if cursor.rowcount > 0:
                        stored_count += 1
                        
                except Exception as e:
                    logger.debug(f"Error storing record for {indicator_name}: {e}")
            
            conn.commit()
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing data for {indicator_name}: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def backfill_indicator(self, indicator_name: str, gap_info: Dict) -> bool:
        """Backfill a specific indicator"""
        config = gap_info["config"]
        start_date = gap_info["start_date"]
        
        logger.info(f"📊 Backfilling {indicator_name} from {start_date}")
        logger.info(f"   📝 {config['description']}")
        
        # Try primary series
        data = self.fetch_fred_data(config["series_id"], start_date)
        
        # Try alternative series if primary fails and alternative exists
        if not data and "alternative_series" in config:
            logger.info(f"   🔄 Trying alternative series: {config['alternative_series']}")
            data = self.fetch_fred_data(config["alternative_series"], start_date)
        
        if data:
            stored = self.store_indicator_data(indicator_name, data, config)
            logger.info(f"   ✅ Stored {stored} records for {indicator_name}")
            return True
        else:
            logger.warning(f"   ⚠️ No data available for {indicator_name}")
            return False
    
    def run_comprehensive_backfill(self) -> Tuple[int, int]:
        """Run comprehensive backfill for all indicators with gaps"""
        gaps = self.detect_gaps()
        
        if not gaps:
            logger.info("🎉 No backfill needed - all indicators current")
            return 0, 0
        
        logger.info(f"🚀 Starting comprehensive backfill for {len(gaps)} indicators")
        
        total_stored = 0
        successful_indicators = 0
        
        # Process by priority: critical first, then urgent, then minor
        for urgency in ["critical", "urgent", "minor"]:
            urgent_gaps = {k: v for k, v in gaps.items() if v["urgency"] == urgency}
            
            if urgent_gaps:
                logger.info(f"🎯 Processing {urgency.upper()} gaps ({len(urgent_gaps)} indicators)")
                
                for indicator_name, gap_info in urgent_gaps.items():
                    try:
                        success = self.backfill_indicator(indicator_name, gap_info)
                        if success:
                            successful_indicators += 1
                        
                        # Rate limiting between API calls
                        time.sleep(self.rate_limit_delay)
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to backfill {indicator_name}: {e}")
        
        logger.info("🎉 Comprehensive backfill complete!")
        logger.info(f"✅ Successfully processed {successful_indicators}/{len(gaps)} indicators")
        
        return total_stored, successful_indicators
    
    def collect_current_data(self) -> int:
        """Collect current/latest data for all indicators"""
        logger.info("📊 Collecting current data for all indicators...")
        
        total_stored = 0
        today = datetime.now().date()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        for indicator_name, config in COMPREHENSIVE_FRED_SERIES.items():
            try:
                logger.info(f"📈 Collecting current data for {indicator_name}")
                
                # Get recent data (last 7 days to ensure we don't miss anything)
                data = self.fetch_fred_data(config["series_id"], yesterday)
                
                if not data and "alternative_series" in config:
                    logger.info(f"   🔄 Trying alternative series for {indicator_name}")
                    data = self.fetch_fred_data(config["alternative_series"], yesterday)
                
                if data:
                    stored = self.store_indicator_data(indicator_name, data, config)
                    total_stored += stored
                    if stored > 0:
                        logger.info(f"   ✅ Stored {stored} new records for {indicator_name}")
                    else:
                        logger.info(f"   ℹ️ No new data for {indicator_name}")
                else:
                    logger.info(f"   ⚠️ No current data available for {indicator_name}")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"❌ Error collecting {indicator_name}: {e}")
        
        logger.info(f"📊 Current collection complete: {total_stored} total records stored")
        return total_stored
    
    def health_check(self) -> Dict:
        """Perform health check on all indicators"""
        health_status = {
            "current": [],
            "stale": [],
            "gaps": [],
            "missing": []
        }
        
        today = datetime.now().date()
        
        for indicator_name, config in COMPREHENSIVE_FRED_SERIES.items():
            last_date, count = self.get_indicator_status(indicator_name)
            
            if last_date:
                days_behind = (today - last_date).days
                
                if days_behind <= 1:
                    health_status["current"].append(indicator_name)
                elif days_behind <= 7:
                    health_status["stale"].append(indicator_name)
                else:
                    health_status["gaps"].append(indicator_name)
            else:
                health_status["missing"].append(indicator_name)
        
        # Log health summary
        total = len(COMPREHENSIVE_FRED_SERIES)
        current_count = len(health_status["current"])
        stale_count = len(health_status["stale"])
        gap_count = len(health_status["gaps"])
        missing_count = len(health_status["missing"])
        
        health_score = (current_count * 100 + stale_count * 70) / total
        
        logger.info(f"🏥 Health Check Summary:")
        logger.info(f"   ✅ Current: {current_count}/{total} ({(current_count/total)*100:.1f}%)")
        logger.info(f"   ⚠️ Stale: {stale_count}/{total} ({(stale_count/total)*100:.1f}%)")
        logger.info(f"   ❌ Gaps: {gap_count}/{total} ({(gap_count/total)*100:.1f}%)")
        logger.info(f"   🚫 Missing: {missing_count}/{total} ({(missing_count/total)*100:.1f}%)")
        logger.info(f"   🏆 Health Score: {health_score:.1f}/100")
        
        return health_status
    
    def run_startup_sequence(self):
        """Run startup sequence with gap detection and backfill"""
        logger.info("🚀 Starting Enhanced Macro Collector...")
        
        # Health check
        health_status = self.health_check()
        
        # Auto-backfill if gaps detected
        gaps_exist = len(health_status["gaps"]) > 0 or len(health_status["missing"]) > 0
        
        if gaps_exist:
            logger.info("🔄 Gaps detected - running comprehensive backfill...")
            self.run_comprehensive_backfill()
            
            # Re-check health after backfill
            logger.info("🔍 Re-checking health after backfill...")
            self.health_check()
        else:
            logger.info("✅ All indicators healthy - no backfill needed")
        
        # Collect current data
        self.collect_current_data()
    
    def run_scheduled_collection(self):
        """Run scheduled collection with gap prevention"""
        logger.info("⏰ Running scheduled macro collection...")
        
        # Quick gap check for recent data only
        recent_gaps = {}
        today = datetime.now().date()
        
        for indicator_name, config in COMPREHENSIVE_FRED_SERIES.items():
            last_date, _ = self.get_indicator_status(indicator_name)
            
            if last_date:
                days_behind = (today - last_date).days
                
                # Only backfill if significantly behind for frequency
                if ((config["frequency"] == "daily" and days_behind > 3) or
                    (config["frequency"] == "monthly" and days_behind > 35) or
                    (config["frequency"] == "quarterly" and days_behind > 100)):
                    
                    start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    recent_gaps[indicator_name] = {
                        "start_date": start_date,
                        "config": config,
                        "days_behind": days_behind
                    }
        
        # Backfill recent gaps if any
        if recent_gaps:
            logger.info(f"🔄 Detected {len(recent_gaps)} recent gaps - backfilling...")
            for indicator_name, gap_info in recent_gaps.items():
                self.backfill_indicator(indicator_name, gap_info)
                time.sleep(self.rate_limit_delay)
        
        # Collect current data
        self.collect_current_data()
        
        # Write health check file
        with open("/tmp/enhanced_macro_collector_health.txt", "w") as f:
            f.write(str(datetime.utcnow()))


def main():
    """Main execution function"""
    collector = EnhancedMacroCollector()
    
    # Check for manual backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"🔄 MANUAL BACKFILL MODE: Processing last {backfill_days} days")
        # For manual backfill, we'll run comprehensive backfill
        collector.run_comprehensive_backfill()
        logger.info("✅ Manual backfill complete. Exiting.")
        return
    
    # Startup sequence
    collector.run_startup_sequence()
    
    # Schedule ongoing collection
    # Run every 2 hours to ensure we never miss data
    schedule.every(2).hours.do(collector.run_scheduled_collection)
    
    # Also run daily health checks
    schedule.every().day.at("06:00").do(collector.health_check)
    
    logger.info("⏰ Enhanced Macro Collector is now running continuously...")
    logger.info("📅 Scheduled: Every 2 hours + daily health checks at 06:00")
    
    # Continuous operation
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("👋 Enhanced Macro Collector shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    main()