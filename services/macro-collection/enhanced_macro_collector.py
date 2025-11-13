#!/usr/bin/env python3
"""
Enhanced Macro Indicators Collector Service

This service collects macroeconomic indicators with:
- Comprehensive FRED API integration
- Dynamic indicator management
- Historical backfill capabilities
- Gap detection and healing
- Multi-frequency data collection (daily, weekly, monthly, quarterly)
"""

import os
import sys
import logging
import time
import requests
import mysql.connector
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Set, Tuple
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFrequency(Enum):
    """Data collection frequency types"""
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

@dataclass
class MacroIndicator:
    """Macro indicator configuration"""
    name: str
    fred_series_id: str
    frequency: DataFrequency
    description: str
    category: str
    active: bool = True
    
class EnhancedMacroService:
    """Enhanced macro indicators collection service"""
    
    def __init__(self):
        """Initialize the enhanced macro service"""
        self.setup_database()
        self.setup_fred_api()
        self.load_indicators()
        
        # Collection stats
        self.stats = {
            "total_collected": 0,
            "last_collection": None,
            "collection_errors": 0,
            "indicators_active": 0,
            "last_gap_check": None,
            "gap_days_detected": 0,
            "backfill_records": 0,
            "health_score": 0.0,
            "api_requests": 0,
            "api_errors": 0,
        }
        
        # Rate limiting
        self.request_delay = 1.0  # FRED API rate limit
        self.max_retries = 3
        
    def setup_database(self):
        """Setup database connection"""
        self.db_config = {
            "host": os.getenv("DB_HOST", "172.22.32.1"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "user": os.getenv("DB_USER", "macro_collector"),
            "password": os.getenv("DB_PASSWORD", "99Rules!"),
            "database": os.getenv("DB_NAME", "crypto_prices")
        }
        
    def setup_fred_api(self):
        """Setup FRED API configuration"""
        self.fred_api_key = os.getenv("FRED_API_KEY", "35478996c5e061d0fc99fc73f5ce348d")
        self.fred_base_url = "https://api.stlouisfed.org/fred"
        
        if not self.fred_api_key:
            logger.error("❌ FRED_API_KEY not configured")
            raise ValueError("FRED API key is required")
            
    def load_indicators(self):
        """Load macro indicators configuration"""
        self.indicators = [
            # Daily Indicators
            MacroIndicator(
                name="10Y_TREASURY",
                fred_series_id="DGS10",
                frequency=DataFrequency.DAILY,
                description="10-Year Treasury Constant Maturity Rate",
                category="interest_rates"
            ),
            MacroIndicator(
                name="2Y_TREASURY", 
                fred_series_id="DGS2",
                frequency=DataFrequency.DAILY,
                description="2-Year Treasury Constant Maturity Rate",
                category="interest_rates"
            ),
            MacroIndicator(
                name="USD_JPY",
                fred_series_id="DEXJPUS",
                frequency=DataFrequency.DAILY,
                description="US Dollar to Japanese Yen Exchange Rate",
                category="exchange_rates"
            ),
            MacroIndicator(
                name="USD_EUR",
                fred_series_id="DEXUSEU", 
                frequency=DataFrequency.DAILY,
                description="US Dollar to Euro Exchange Rate",
                category="exchange_rates"
            ),
            MacroIndicator(
                name="VIX",
                fred_series_id="VIXCLS",
                frequency=DataFrequency.DAILY,
                description="CBOE Volatility Index",
                category="volatility"
            ),
            MacroIndicator(
                name="DOLLAR_INDEX",
                fred_series_id="DTWEXBGS",
                frequency=DataFrequency.DAILY,
                description="Trade Weighted US Dollar Index",
                category="exchange_rates"
            ),
            
            # Weekly Indicators
            MacroIndicator(
                name="UNEMPLOYMENT_CLAIMS",
                fred_series_id="ICSA",
                frequency=DataFrequency.WEEKLY,
                description="Initial Claims for Unemployment Insurance",
                category="labor_market"
            ),
            
            # Monthly Indicators
            MacroIndicator(
                name="UNEMPLOYMENT_RATE",
                fred_series_id="UNRATE",
                frequency=DataFrequency.MONTHLY,
                description="Civilian Unemployment Rate",
                category="labor_market"
            ),
            MacroIndicator(
                name="CPI_INFLATION",
                fred_series_id="CPIAUCSL",
                frequency=DataFrequency.MONTHLY,
                description="Consumer Price Index for All Urban Consumers",
                category="inflation"
            ),
            MacroIndicator(
                name="FEDERAL_FUNDS_RATE",
                fred_series_id="FEDFUNDS",
                frequency=DataFrequency.MONTHLY,
                description="Federal Funds Effective Rate",
                category="interest_rates"
            ),
            MacroIndicator(
                name="INDUSTRIAL_PRODUCTION",
                fred_series_id="INDPRO",
                frequency=DataFrequency.MONTHLY,
                description="Industrial Production Index",
                category="economic_activity"
            ),
            MacroIndicator(
                name="RETAIL_SALES",
                fred_series_id="RSAFS",
                frequency=DataFrequency.MONTHLY,
                description="Advance Retail Sales",
                category="economic_activity"
            ),
            MacroIndicator(
                name="HOUSING_STARTS",
                fred_series_id="HOUST",
                frequency=DataFrequency.MONTHLY,
                description="Housing Starts",
                category="housing"
            ),
            MacroIndicator(
                name="CONSUMER_CONFIDENCE",
                fred_series_id="UMCSENT",
                frequency=DataFrequency.MONTHLY,
                description="University of Michigan Consumer Sentiment",
                category="sentiment"
            ),
            
            # Quarterly Indicators
            MacroIndicator(
                name="REAL_GDP",
                fred_series_id="GDPC1",
                frequency=DataFrequency.QUARTERLY,
                description="Real Gross Domestic Product",
                category="economic_activity"
            ),
            MacroIndicator(
                name="GDP_DEFLATOR",
                fred_series_id="GDPDEF",
                frequency=DataFrequency.QUARTERLY,
                description="Gross Domestic Product Implicit Price Deflator",
                category="inflation"
            ),
        ]
        
        active_indicators = [i for i in self.indicators if i.active]
        self.stats["indicators_active"] = len(active_indicators)
        logger.info(f"✅ Loaded {len(active_indicators)} active macro indicators")
        
    def get_connection(self):
        """Get database connection with error handling"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def fetch_fred_data(self, indicator: MacroIndicator, start_date: date = None, end_date: date = None) -> List[Dict]:
        """Fetch data from FRED API for a specific indicator"""
        try:
            self.stats["api_requests"] += 1
            
            params = {
                "series_id": indicator.fred_series_id,
                "api_key": self.fred_api_key,
                "file_type": "json",
                "sort_order": "asc"
            }
            
            if start_date:
                params["observation_start"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["observation_end"] = end_date.strftime("%Y-%m-%d")
                
            url = f"{self.fred_base_url}/series/observations"
            
            logger.info(f"📡 Fetching {indicator.name} from FRED API")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if not observations:
                logger.warning(f"⚠️  No observations returned for {indicator.name}")
                return []
                
            results = []
            for obs in observations:
                try:
                    value = obs.get("value")
                    if value != "." and value is not None:  # FRED uses "." for missing values
                        obs_date = datetime.strptime(obs.get("date"), "%Y-%m-%d").date()
                        results.append({
                            "indicator_name": indicator.name,
                            "date": obs_date,
                            "value": float(value),
                            "fred_series_id": indicator.fred_series_id,
                            "frequency": indicator.frequency.value,
                            "category": indicator.category
                        })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not parse observation for {indicator.name}: {e}")
                    continue
                    
            logger.info(f"✅ Retrieved {len(results)} observations for {indicator.name}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error fetching {indicator.name}: {e}")
            self.stats["api_errors"] += 1
            return []
            
    def store_indicator_data(self, data_points: List[Dict]) -> int:
        """Store indicator data with duplicate detection"""
        if not data_points:
            return 0
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                stored_count = 0
                
                for point in data_points:
                    try:
                        # Insert with ON DUPLICATE KEY UPDATE
                        insert_sql = """
                        INSERT INTO macro_indicators (
                            indicator_name, indicator_date, value, 
                            fred_series_id, frequency, category,
                            data_source, collected_at, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
                        ) ON DUPLICATE KEY UPDATE
                            value = VALUES(value),
                            updated_at = NOW()
                        """
                        
                        cursor.execute(insert_sql, (
                            point["indicator_name"],
                            point["date"],
                            point["value"],
                            point["fred_series_id"],
                            point["frequency"],
                            point["category"],
                            "FRED_API"
                        ))
                        
                        if cursor.rowcount > 0:
                            stored_count += 1
                            
                    except Exception as e:
                        logger.error(f"❌ Error storing data point: {e}")
                        continue
                        
                conn.commit()
                logger.info(f"✅ Stored {stored_count} macro indicator records")
                return stored_count
                
        except Exception as e:
            logger.error(f"❌ Error storing indicator data: {e}")
            return 0
            
    def run_collection_cycle(self) -> Dict:
        """Run one complete collection cycle for all indicators"""
        logger.info("🔄 Starting macro indicators collection cycle...")
        start_time = datetime.now()
        
        total_collected = 0
        total_stored = 0
        indicators_processed = 0
        
        # Get appropriate lookback period based on frequency
        lookback_days = {
            DataFrequency.DAILY: 7,      # 1 week
            DataFrequency.WEEKLY: 14,    # 2 weeks
            DataFrequency.MONTHLY: 35,   # ~1 month
            DataFrequency.QUARTERLY: 95, # ~3 months
        }
        
        for indicator in self.indicators:
            if not indicator.active:
                continue
                
            try:
                # Calculate date range based on frequency
                end_date = date.today()
                days_back = lookback_days.get(indicator.frequency, 30)
                start_date = end_date - timedelta(days=days_back)
                
                # Fetch data
                data_points = self.fetch_fred_data(indicator, start_date, end_date)
                
                if data_points:
                    stored = self.store_indicator_data(data_points)
                    total_collected += len(data_points)
                    total_stored += stored
                    
                indicators_processed += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error processing {indicator.name}: {e}")
                self.stats["collection_errors"] += 1
                continue
                
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update stats
        self.stats["total_collected"] += total_collected
        self.stats["last_collection"] = end_time
        
        result = {
            "status": "completed",
            "duration_seconds": duration,
            "indicators_processed": indicators_processed,
            "data_points_collected": total_collected,
            "records_stored": total_stored,
            "api_requests": self.stats["api_requests"],
            "api_errors": self.stats["api_errors"],
            "timestamp": end_time.isoformat()
        }
        
        logger.info(f"✅ Collection cycle completed: {result}")
        return result
        
    def detect_data_gaps(self) -> Optional[float]:
        """Detect gaps in macro indicator data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check latest data across all indicators
                cursor.execute("""
                    SELECT 
                        MAX(indicator_date) as last_date,
                        COUNT(DISTINCT indicator_name) as active_indicators,
                        COUNT(*) as total_records
                    FROM macro_indicators 
                    WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                """)
                
                result = cursor.fetchone()
                
                if result and result[0]:
                    last_date = result[0]
                    now_date = date.today()
                    gap_days = (now_date - last_date).days
                    
                    self.stats["gap_days_detected"] = gap_days
                    self.stats["last_gap_check"] = datetime.now()
                    
                    logger.info(f"📊 Gap analysis: {gap_days} days since last data")
                    return gap_days
                else:
                    logger.info("ℹ️  No recent macro data found")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error detecting gaps: {e}")
            return None
            
    def get_missing_dates_by_indicator(self, indicator: MacroIndicator, start_date: date, end_date: date) -> List[date]:
        """Get missing dates for a specific indicator"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get existing dates for this indicator
                cursor.execute("""
                    SELECT DISTINCT indicator_date 
                    FROM macro_indicators 
                    WHERE indicator_name = %s 
                    AND indicator_date BETWEEN %s AND %s
                    ORDER BY indicator_date
                """, (indicator.name, start_date, end_date))
                
                existing_dates = {row[0] for row in cursor.fetchall()}
                
                # Generate expected dates based on frequency
                expected_dates = self.generate_expected_dates(indicator.frequency, start_date, end_date)
                missing_dates = [d for d in expected_dates if d not in existing_dates]
                
                return missing_dates
                
        except Exception as e:
            logger.error(f"❌ Error finding missing dates for {indicator.name}: {e}")
            return []
            
    def generate_expected_dates(self, frequency: DataFrequency, start_date: date, end_date: date) -> List[date]:
        """Generate expected dates based on data frequency"""
        dates = []
        current = start_date
        
        if frequency == DataFrequency.DAILY:
            while current <= end_date:
                # Skip weekends for daily data (markets closed)
                if current.weekday() < 5:  # Monday=0, Sunday=6
                    dates.append(current)
                current += timedelta(days=1)
                
        elif frequency == DataFrequency.WEEKLY:
            # Weekly data typically on specific day (Friday)
            while current <= end_date:
                if current.weekday() == 4:  # Friday
                    dates.append(current)
                current += timedelta(days=1)
                
        elif frequency == DataFrequency.MONTHLY:
            # Monthly data typically end of month
            while current.year <= end_date.year and (current.year < end_date.year or current.month <= end_date.month):
                # Last day of month
                if current.month == 12:
                    next_month = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    next_month = current.replace(month=current.month + 1, day=1)
                last_day = next_month - timedelta(days=1)
                dates.append(last_day)
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
                    
        elif frequency == DataFrequency.QUARTERLY:
            # Quarterly data at end of quarters (Mar, Jun, Sep, Dec)
            quarter_months = [3, 6, 9, 12]
            year = start_date.year
            while year <= end_date.year:
                for month in quarter_months:
                    if year == end_date.year and month > end_date.month:
                        break
                    if year == start_date.year and month < start_date.month:
                        continue
                    # Last day of quarter
                    if month == 12:
                        quarter_end = date(year, month, 31)
                    elif month in [3, 6, 9]:
                        next_month = date(year, month + 1, 1)
                        quarter_end = next_month - timedelta(days=1)
                    dates.append(quarter_end)
                year += 1
                
        return dates
        
    def backfill_historical_data(self, start_date: date, end_date: date = None) -> int:
        """Backfill macro data for specified date range"""
        if end_date is None:
            end_date = date.today()
            
        logger.info(f"🔄 Starting macro backfill from {start_date} to {end_date}")
        
        total_backfilled = 0
        
        for indicator in self.indicators:
            if not indicator.active:
                continue
                
            try:
                logger.info(f"🔄 Backfilling {indicator.name}...")
                
                # Fetch historical data
                data_points = self.fetch_fred_data(indicator, start_date, end_date)
                
                if data_points:
                    stored = self.store_indicator_data(data_points)
                    total_backfilled += stored
                    logger.info(f"   ✅ {indicator.name}: {stored} records backfilled")
                    
                # Rate limiting
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"❌ Error backfilling {indicator.name}: {e}")
                continue
                
        self.stats["backfill_records"] = total_backfilled
        logger.info(f"✅ Backfill completed: {total_backfilled} total records")
        return total_backfilled
        
    def auto_gap_detection_and_healing(self):
        """Automatically detect and heal data gaps"""
        logger.info("🔍 Running automatic gap detection and healing...")
        
        gap_days = self.detect_data_gaps()
        
        if gap_days is not None and gap_days > 1:  # More than 1 day gap
            logger.warning(f"⚠️  Gap detected: {gap_days} days since last data")
            
            # Limit backfill to reasonable period
            backfill_days = min(gap_days + 7, 365)  # Max 1 year
            start_date = date.today() - timedelta(days=backfill_days)
            
            logger.info(f"🔧 Auto-healing: backfilling last {backfill_days} days")
            self.backfill_historical_data(start_date)
            
        elif gap_days is None:
            logger.info("ℹ️  No previous data found - running initial collection")
            # Initial backfill for 30 days
            start_date = date.today() - timedelta(days=30)
            self.backfill_historical_data(start_date)
        else:
            logger.info(f"✅ No significant gaps detected ({gap_days} days)")
            
    def calculate_health_score(self) -> float:
        """Calculate service health score"""
        try:
            health_score = 100.0
            
            # Check data freshness
            gap_days = self.detect_data_gaps()
            if gap_days:
                if gap_days > 7:
                    health_score -= min(40, gap_days * 2)
                elif gap_days > 3:
                    health_score -= gap_days * 5
                    
            # Check API success rate
            total_requests = self.stats["api_requests"]
            if total_requests > 0:
                error_rate = self.stats["api_errors"] / total_requests
                health_score -= error_rate * 30
                
            # Check indicator coverage
            if self.stats["indicators_active"] < 10:
                health_score -= (10 - self.stats["indicators_active"]) * 3
                
            health_score = max(0.0, health_score)
            self.stats["health_score"] = health_score
            
            return health_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating health score: {e}")
            return 0.0

# Enhanced Macro Collector with FastAPI interface
class EnhancedMacroCollector:
    """Enhanced macro indicators collector with FastAPI interface"""
    
    def __init__(self):
        self.service = EnhancedMacroService()
        self.app = FastAPI(
            title="Enhanced Macro Indicators Collector",
            description="Advanced macroeconomic indicators collection service",
            version="2.0.0"
        )
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "enhanced-macro-collector"}
            
        @self.app.get("/status")
        def status():
            gap_days = self.service.detect_data_gaps()
            health_score = self.service.calculate_health_score()
            
            return {
                "service": "enhanced-macro-collector",
                "stats": self.service.stats,
                "indicators_active": len([i for i in self.service.indicators if i.active]),
                "gap_days": gap_days,
                "health_score": health_score,
                "data_freshness": "healthy" if (gap_days or 0) < 3 else "stale",
                "timestamp": datetime.now().isoformat()
            }
            
        @self.app.get("/indicators")
        def get_indicators():
            """Get all configured indicators"""
            return {
                "indicators": [
                    {
                        "name": i.name,
                        "fred_series_id": i.fred_series_id,
                        "frequency": i.frequency.value,
                        "description": i.description,
                        "category": i.category,
                        "active": i.active
                    }
                    for i in self.service.indicators
                ],
                "total": len(self.service.indicators),
                "active": len([i for i in self.service.indicators if i.active])
            }
            
        @self.app.post("/collect")
        def collect_indicators(background_tasks: BackgroundTasks):
            """Trigger macro indicators collection"""
            background_tasks.add_task(self.service.run_collection_cycle)
            return {"status": "started", "message": "Macro collection initiated"}
            
        @self.app.post("/backfill")
        def backfill_data(
            days: int = 30,
            background_tasks: BackgroundTasks = None
        ):
            """Trigger historical backfill"""
            if days > 365:
                return {"error": "Maximum backfill period is 365 days"}
                
            start_date = date.today() - timedelta(days=days)
            
            if background_tasks:
                background_tasks.add_task(
                    self.service.backfill_historical_data,
                    start_date
                )
                
            return {
                "status": "started",
                "message": f"Backfill initiated for {days} days",
                "start_date": start_date.isoformat()
            }
            
        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and auto-heal"""
            self.service.auto_gap_detection_and_healing()
            return {
                "status": "completed",
                "gap_days": self.service.stats.get("gap_days_detected", 0),
                "health_score": self.service.stats.get("health_score", 0)
            }

# Create the enhanced service instance
macro_collector = EnhancedMacroCollector()
app = macro_collector.app

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Macro Indicators Collector")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind to")
    parser.add_argument("--auto-heal", action="store_true", default=True,
                       help="Run automatic gap detection on startup")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Enhanced Macro Indicators Collector on {args.host}:{args.port}")
    
    # Run automatic gap detection and healing on startup
    if args.auto_heal:
        logger.info("🔍 Running startup gap detection and healing...")
        macro_collector.service.auto_gap_detection_and_healing()
        logger.info("✅ Startup gap check complete")
        
    uvicorn.run(app, host=args.host, port=args.port)