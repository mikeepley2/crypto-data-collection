#!/usr/bin/env python3
"""
Premium OHLC Collector with Universal Symbol Normalization
- Uses universal symbol normalizer for cross-exchange compatibility
- Premium CoinGecko API key for better rate limits
- Fills the identified OHLC data gap (Sept 30 → Present)
- Collects ongoing OHLC data for all active symbols
"""

import os
import time
import mysql.connector
import requests
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import threading
import schedule

# Import centralized scheduling configuration
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None
    create_schedule_for_collector = None

# Import our universal symbol normalizer
from shared_symbol_normalizer import UniversalSymbolNormalizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PremiumOHLCCollector:
    """Premium OHLC collector with universal symbol support"""
    
    def __init__(self):
        # Premium CoinGecko API configuration
        self.api_key = os.getenv('COINGECKO_PREMIUM_API_KEY', 'CG-94NCcVD2euxaGTZe94bS2oYz')
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        
        # Import centralized database configuration
        try:
            from shared.database_config import get_db_config
            self.db_config = get_db_config()
            logger.info("✅ Using centralized database configuration")
        except ImportError:
            # Fallback to environment variables for local development
            self.db_config = {
                'host': os.getenv('DB_HOST', '172.22.32.1'),
                'port': int(os.getenv('DB_PORT', '3306')),
                'user': os.getenv('DB_USER', 'news_collector'),
                'password': os.getenv('DB_PASSWORD', '99Rules!'),
                'database': os.getenv('DB_NAME', 'crypto_prices'),
            }
            logger.info("⚠️  Using fallback database configuration")
        
        # Statistics tracking
        self.stats = {
            "total_collected": 0,
            "last_collection": None,
            "collection_errors": 0,
            "symbols_processed": 0,
            "last_gap_check": None,
            "gap_hours_detected": 0,
            "backfill_records": 0,
            "health_score": 0.0,
        }
        
        # Initialize universal symbol normalizer
        try:
            self.normalizer = UniversalSymbolNormalizer(self.db_config)
            logger.info("✅ Universal symbol normalizer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize normalizer: {e}")
            raise
        
        # API session with premium headers
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'User-Agent': 'Premium-OHLC-Collector/1.0'
        })
        
        # Premium rate limiting - 500 calls/minute
        self.rate_limit_delay = 0.15  # 150ms between calls
        self.last_request_time = 0
        
        logger.info("🚀 Premium OHLC Collector initialized with universal symbols")
    
    def rate_limit(self):
        """Enforce premium rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_active_symbols(self) -> List[Dict[str, str]]:
        """Get active symbols using universal normalizer"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Get symbols with universal format and CoinGecko IDs
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets
                WHERE is_active = 1 
                AND coingecko_id IS NOT NULL 
                AND coingecko_id != ''
                AND symbol IS NOT NULL
                ORDER BY COALESCE(market_cap_rank, 999999), symbol
                LIMIT 100
            """)
            
            symbols_data = []
            for symbol, coingecko_id, name in cursor.fetchall():
                # Normalize symbol to universal format
                normalized_symbol = self.normalizer.normalize_symbol(symbol)
                
                if normalized_symbol:
                    symbols_data.append({
                        'symbol': normalized_symbol,  # Use universal format
                        'original_symbol': symbol,
                        'coingecko_id': coingecko_id,
                        'name': name
                    })
            
            cursor.close()
            connection.close()
            
            logger.info(f"📊 Retrieved {len(symbols_data)} active symbols with universal normalization")
            return symbols_data
            
        except Exception as e:
            logger.error(f"❌ Error getting active symbols: {e}")
            return []
    
    def get_ohlc_coverage_gaps(self) -> Dict[str, datetime]:
        """Identify symbols with OHLC data gaps"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Find symbols with missing recent data (last 7 days)
            cursor.execute("""
                SELECT symbol, MAX(timestamp_iso) as last_ohlc
                FROM ohlc_data
                GROUP BY symbol
                HAVING MAX(timestamp_iso) < DATE_SUB(NOW(), INTERVAL 7 DAY)
                OR MAX(timestamp_iso) IS NULL
                ORDER BY last_ohlc ASC
            """)
            
            gaps = {}
            for symbol, last_ohlc in cursor.fetchall():
                gaps[symbol] = last_ohlc or datetime(2020, 1, 1)
            
            cursor.close()
            connection.close()
            
            logger.info(f"📊 Found {len(gaps)} symbols with OHLC data gaps")
            return gaps
            
        except Exception as e:
            logger.error(f"❌ Error checking OHLC coverage: {e}")
            return {}
    
    def fetch_ohlc_data(self, coingecko_id: str, days: int = 90) -> Optional[List]:
        """Fetch OHLC data from CoinGecko Premium API"""
        self.rate_limit()
        
        try:
            url = f"{self.base_url}/coins/{coingecko_id}/ohlc"
            
            # CoinGecko OHLC endpoint uses specific values: 1, 7, 14, 30, 90, 180, 365
            allowed_days = [1, 7, 14, 30, 90, 180, 365]
            api_days = min(allowed_days, key=lambda x: abs(x - days) if x >= days else float('inf'))
            
            params = {
                'vs_currency': 'usd',
                'days': api_days,
                'x_cg_pro_api_key': self.api_key  # Add API key to params
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"Rate limited for {coingecko_id}, backing off...")
                time.sleep(5)
                return None
            elif response.status_code == 401:
                logger.error(f"Authentication failed for {coingecko_id}")
                return None
            else:
                logger.warning(f"API error for {coingecko_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching OHLC for {coingecko_id}: {e}")
            return None
    
    def store_ohlc_records(self, symbol: str, coingecko_id: str, ohlc_data: List, 
                          since_date: Optional[datetime] = None) -> int:
        """Store OHLC records using universal symbol format"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Filter data if since_date is provided
            cutoff_timestamp = since_date.timestamp() * 1000 if since_date else 0
            
            insert_query = """
                INSERT IGNORE INTO ohlc_data 
                (symbol, coin_id, timestamp_unix, timestamp_iso, 
                 open_price, high_price, low_price, close_price, 
                 volume, data_source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            records_inserted = 0
            
            # Validate OHLC data to prevent NULL values
            logger.info(f"🔍 Validating {len(ohlc_data)} OHLC records for {symbol}")
            
            for record in ohlc_data:
                try:
                    timestamp_ms = record[0]
                    
                    # Skip old data if filtering
                    if timestamp_ms < cutoff_timestamp:
                        continue
                    
                    timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    # Validate OHLC data structure
                    if len(record) < 5:
                        logger.warning(f"⚠️  Incomplete OHLC record for {symbol}: {record}")
                        continue
                    
                    # Extract and validate price data
                    open_price = record[1]
                    high_price = record[2]
                    low_price = record[3]
                    close_price = record[4]
                    
                    # Skip records with invalid price data
                    if any(price is None or price <= 0 for price in [open_price, high_price, low_price, close_price]):
                        logger.warning(f"⚠️  Invalid price data for {symbol} at {timestamp_dt}: O={open_price}, H={high_price}, L={low_price}, C={close_price}")
                        continue
                    
                    # Handle volume data - ensure it's never NULL
                    volume = 0.0  # Default to 0 if no volume data
                    if len(record) > 5 and record[5] is not None:
                        try:
                            volume = float(record[5])
                            if volume < 0:
                                volume = 0.0  # Ensure non-negative volume
                        except (ValueError, TypeError):
                            volume = 0.0
                    
                    values = (
                        symbol,  # Universal format symbol
                        coingecko_id,
                        int(timestamp_ms),
                        timestamp_dt,
                        float(open_price),  # open
                        float(high_price),  # high
                        float(low_price),   # low
                        float(close_price), # close
                        volume,             # volume (never NULL)
                        'premium_ohlc_collector',
                        datetime.now()
                    )
                    
                    cursor.execute(insert_query, values)
                    records_inserted += 1
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Skipping invalid OHLC record for {symbol}: {e}")
                    continue
            
            connection.commit()
            cursor.close()
            connection.close()
            
            if records_inserted > 0:
                logger.info(f"   ✅ Stored {records_inserted} OHLC records for {symbol}")
            
            return records_inserted
            
        except Exception as e:
            logger.error(f"❌ Error storing OHLC data for {symbol}: {e}")
            self.stats["collection_errors"] += 1
            return 0
    
    def detect_gap(self) -> Optional[float]:
        """
        Detect gaps in OHLC data collection
        Returns number of hours since last update, or None if no data exists
        """
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT MAX(date) as last_update
                FROM ohlc_data
            """)
            
            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result and result[0]:
                last_update = result[0]
                if isinstance(last_update, str):
                    last_update = datetime.fromisoformat(last_update)
                elif hasattr(last_update, 'date'):
                    last_update = datetime.combine(last_update, datetime.min.time())
                
                now = datetime.utcnow()
                gap_hours = (now - last_update).total_seconds() / 3600
                self.stats["gap_hours_detected"] = gap_hours
                self.stats["last_gap_check"] = now
                return gap_hours
            else:
                logger.info("No existing OHLC data found - first run")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting gap: {e}")
            return None

    def calculate_health_score(self) -> float:
        """Calculate health score based on data freshness and collection success"""
        try:
            gap_hours = self.detect_gap()
            
            # Base score starts at 100
            health_score = 100.0
            
            # Deduct points for data gaps
            if gap_hours:
                if gap_hours > 48:  # More than 2 days old
                    health_score -= min(60, gap_hours)  # Max 60 point deduction
                elif gap_hours > 24:  # More than 1 day old
                    health_score -= gap_hours * 1.5
            
            # Deduct points for collection errors
            total_attempts = max(1, self.stats["symbols_processed"])
            error_ratio = self.stats["collection_errors"] / total_attempts
            health_score -= error_ratio * 25  # Max 25 point deduction
            
            # Ensure score doesn't go below 0
            health_score = max(0.0, health_score)
            
            self.stats["health_score"] = health_score
            return health_score
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0

    def auto_gap_detection_and_backfill(self):
        """
        Automatically detect gaps and backfill if necessary
        Called on startup and periodically
        """
        logger.info("Running automatic gap detection...")
        
        gap_hours = self.detect_gap()
        if gap_hours:
            # Use centralized scheduling config with fallback
            if get_collector_schedule:
                config = get_collector_schedule('ohlc')
                collection_interval_hours = config['frequency_hours']
            else:
                collection_interval_hours = 24  # Fallback: OHLC data collected daily
            
            if gap_hours > collection_interval_hours:
                gap_days = min(int(gap_hours / 24) + 1, 30)  # Limit to 30 days max
                logger.warning(f"⚠️  Gap detected: {gap_hours:.1f} hours since last update")
                logger.info(f"🔄 Auto-backfilling last {gap_days} days to fill gap...")
                
                self.backfill_recent_data()
                logger.info("✅ Gap backfill complete")
            else:
                logger.info(f"✅ No significant gap detected ({gap_hours:.1f} hours)")
        else:
            logger.info("ℹ️  No previous data found - running initial collection")
            self.collect_current_data()

    def backfill_recent_data(self):
        """Backfill recent OHLC data gaps"""
        logger.info("🔄 Starting OHLC backfill process...")
        
        active_symbols = self.get_active_symbols()
        if not active_symbols:
            logger.warning("No active symbols found for backfill")
            return
        
        gaps = self.get_ohlc_coverage_gaps()
        
        total_records = 0
        successful_collections = 0
        
        for symbol_info in active_symbols:
            symbol = symbol_info['symbol']
            coingecko_id = symbol_info['coingecko_id']
            
            # Check if this symbol needs backfill
            since_date = gaps.get(symbol)
            if since_date:
                # Calculate days to backfill
                days_to_backfill = min(90, (datetime.now() - since_date).days + 1)
                
                logger.info(f"📈 Backfilling {symbol} from {since_date} ({days_to_backfill} days)...")
                
                ohlc_data = self.fetch_ohlc_data(coingecko_id, days_to_backfill)
                
                if ohlc_data:
                    records = self.store_ohlc_records(symbol, coingecko_id, ohlc_data, since_date)
                    total_records += records
                    if records > 0:
                        successful_collections += 1
                else:
                    logger.warning(f"⚠️ No OHLC data available for {symbol}")
        
        logger.info(f"🎉 Backfill completed: {total_records} records for {successful_collections} symbols")
    
    def collect_current_data(self):
        """Collect current OHLC data for all active symbols"""
        logger.info("📊 Starting current OHLC data collection...")
        
        active_symbols = self.get_active_symbols()
        if not active_symbols:
            logger.warning("No active symbols found for collection")
            return
        
        total_records = 0
        successful_collections = 0
        
        # Collect 2 days of data to ensure we have latest
        for symbol_info in active_symbols:
            symbol = symbol_info['symbol']
            coingecko_id = symbol_info['coingecko_id']
            
            logger.info(f"📈 Collecting current OHLC for {symbol}...")
            
            ohlc_data = self.fetch_ohlc_data(coingecko_id, days=2)
            
            if ohlc_data:
                records = self.store_ohlc_records(symbol, coingecko_id, ohlc_data)
                total_records += records
                if records > 0:
                    successful_collections += 1
            else:
                logger.warning(f"⚠️ No current OHLC data for {symbol}")
        
        logger.info(f"✅ Current collection completed: {total_records} records for {successful_collections} symbols")
        
        # Update statistics
        self.stats["total_collected"] += total_records
        self.stats["symbols_processed"] += len(active_symbols)
        self.stats["last_collection"] = datetime.now()
    
    def run_comprehensive_collection(self):
        """Run comprehensive OHLC collection (backfill + current)"""
        start_time = datetime.now()
        
        logger.info("🚀 STARTING COMPREHENSIVE OHLC COLLECTION")
        logger.info("=" * 60)
        logger.info("Using premium CoinGecko API with universal symbol normalization")
        
        try:
            # First, backfill any gaps
            self.backfill_recent_data()
            
            # Then collect current data
            self.collect_current_data()
            
            # Final status check
            gaps_remaining = self.get_ohlc_coverage_gaps()
            
            elapsed = datetime.now() - start_time
            
            logger.info("=" * 60)
            logger.info("🎉 COMPREHENSIVE OHLC COLLECTION COMPLETE!")
            logger.info(f"⏰ Total time: {elapsed}")
            logger.info(f"📊 Remaining gaps: {len(gaps_remaining)} symbols")
            logger.info(f"✅ Collection using universal symbols: BTC, ETH, ADA, SOL, etc.")
            logger.info("🌐 Data compatible with all major exchanges!")
            
        except KeyboardInterrupt:
            logger.info("🛑 Collection interrupted by user")
        except Exception as e:
            logger.error(f"❌ Collection failed: {e}")
            raise


class OHLCCollectorAPI:
    """FastAPI wrapper for OHLC collector"""
    
    def __init__(self):
        self.collector = PremiumOHLCCollector()
        self.app = FastAPI(
            title="Premium OHLC Collector",
            description="Collects OHLC data with universal symbol support",
            version="1.0.0",
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "premium-ohlc-collector"}
        
        @self.app.get("/status")  
        def status():
            gap_hours = self.collector.detect_gap()
            health_score = self.collector.calculate_health_score()
            
            return {
                "service": "premium-ohlc-collector",
                "stats": self.collector.stats,
                "gap_hours": gap_hours,
                "health_score": health_score,
                "data_freshness": "healthy" if (gap_hours or 0) < 48 else "stale",
            }
        
        @self.app.post("/collect")
        def collect_ohlc(background_tasks: BackgroundTasks):
            """Trigger OHLC collection"""
            background_tasks.add_task(self.collector.collect_current_data)
            return {"status": "started", "message": "OHLC collection initiated"}
        
        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and optionally backfill"""
            self.collector.auto_gap_detection_and_backfill()
            return {
                "status": "completed",
                "gap_hours": self.collector.stats.get("gap_hours_detected", 0),
                "health_score": self.collector.stats.get("health_score", 0),
            }
        
        @self.app.post("/backfill")
        def manual_backfill(background_tasks: BackgroundTasks):
            """Manually trigger backfill"""
            background_tasks.add_task(self.collector.backfill_recent_data)
            return {"status": "started", "message": "Backfill initiated"}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Premium OHLC Collector")
    parser.add_argument("--mode", choices=["collect", "api"], default="collect",
                       help="Run mode: collect (one-time) or api (service)")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8002, help="API port")
    parser.add_argument("--auto-gap-check", action="store_true", default=True,
                       help="Run automatic gap detection on startup")
    
    args = parser.parse_args()
    
    if args.mode == "collect":
        # One-time collection mode
        try:
            collector = PremiumOHLCCollector()
            if args.auto_gap_check:
                logger.info("🔍 Running startup gap detection...")
                collector.auto_gap_detection_and_backfill()
            else:
                collector.run_comprehensive_collection()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            exit(1)
    
    elif args.mode == "api":
        # API service mode
        try:
            api = OHLCCollectorAPI()
            
            # Run startup gap detection
            if args.auto_gap_check:
                logger.info("🔍 Running startup gap detection...")
                api.collector.auto_gap_detection_and_backfill()
                logger.info("✅ Startup gap check complete")
            
            # Schedule daily collection in background
            def background_scheduler():
                # Use centralized scheduling config with fallback
                if create_schedule_for_collector:
                    try:
                        create_schedule_for_collector('ohlc', schedule, api.collector.collect_current_data)
                        logger.info("✅ Using centralized scheduling configuration")
                    except Exception as e:
                        logger.warning(f"Centralized config failed, using fallback: {e}")
                        schedule.every().day.at("02:00").do(api.collector.collect_current_data)
                else:
                    schedule.every().day.at("02:00").do(api.collector.collect_current_data)
                
                schedule.every().hour.do(lambda: None)  # Health check placeholder
                
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            
            # Start background scheduler
            scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
            scheduler_thread.start()
            
            # Start FastAPI server
            logger.info(f"Starting OHLC API service on {args.host}:{args.port}...")
            uvicorn.run(api.app, host=args.host, port=args.port)
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            exit(1)