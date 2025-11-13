#!/usr/bin/env python3
"""
Enhanced OHLC Collector - Production Ready
Collects comprehensive OHLC data with real-time monitoring
Includes production-grade API endpoints, health scoring, and automated gap detection
Matches template standard established by derivatives and technical collectors
"""

import os
import sys
import logging
import mysql.connector
import asyncio
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import schedule
from concurrent.futures import ThreadPoolExecutor

# Dynamic symbol management
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
try:
    from table_config import get_collector_symbols, normalize_symbol_for_exchange
except ImportError:
    logger.warning("Could not import centralized table_config, using fallback")
    get_collector_symbols = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced-ohlc-collector")

class EnhancedOHLCCollector:
    """Production-ready OHLC collector with comprehensive monitoring and FastAPI endpoints"""
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            "host": os.getenv("MYSQL_HOST", "172.22.32.1"),
            "user": os.getenv("MYSQL_USER", "news_collector"),
            "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
            "database": os.getenv("MYSQL_DATABASE", "crypto_prices"),
            "charset": "utf8mb4"
        }
        
        # CoinGecko Premium API configuration
        self.api_key = os.getenv('COINGECKO_PREMIUM_API_KEY', 'CG-94NCcVD2euxaGTZe94bS2oYz')
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        
        # Service configuration
        self.service_name = "Enhanced OHLC Collector"
        self.collection_interval = 3600  # 1 hour (OHLC typical interval)
        self.rate_limit_delay = 0.15  # 150ms between calls (500 calls/minute)
        self.last_request_time = 0
        
        # Initialize session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'x-cg-pro-api-key': self.api_key,
            'accept': 'application/json'
        })
        
        # Load symbols dynamically
        self.symbols = self._load_symbols()
        
        # Statistics tracking
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'ohlc_records_collected': 0,
            'api_calls_made': 0,
            'last_collection': None,
            'last_success': None,
            'last_error': None,
            'database_writes': 0,
            'symbols_processed': 0
        }
        
        # Health tracking
        self.health_metrics = {
            'service_start_time': datetime.now(),
            'consecutive_failures': 0,
            'api_error_count': 0,
            'database_error_count': 0
        }
        
        # FastAPI setup
        self.app = FastAPI(title="Enhanced OHLC Data Collector", version="1.0.0")
        self._setup_api_endpoints()
        
        logger.info(f"🚀 {self.service_name} initialized")
        logger.info(f"📊 Tracking {len(self.symbols)} symbols")
        logger.info(f"🔑 Using CoinGecko Premium API: {self.api_key[:8]}...")

    def _load_symbols(self) -> List[str]:
        """Load symbols from database or configuration"""
        try:
            if get_collector_symbols:
                symbols = get_collector_symbols('ohlc')
                logger.info(f"📊 Loaded {len(symbols)} symbols from centralized config")
                return symbols
            else:
                # Fallback to database query
                return self._get_symbols_from_database()
        except Exception as e:
            logger.error(f"❌ Error loading symbols: {e}")
            return self._get_default_symbols()

    def _get_symbols_from_database(self) -> List[str]:
        """Get symbols with CoinGecko mappings from database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT symbol, coin_id 
                FROM price_data_real 
                WHERE coin_id IS NOT NULL 
                AND coin_id != ''
                ORDER BY symbol
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"📊 Loaded {len(symbols)} symbols from database")
            return symbols[:100]  # Limit to top 100 for performance
            
        except Exception as e:
            logger.error(f"❌ Database symbol loading failed: {e}")
            return self._get_default_symbols()

    def _get_default_symbols(self) -> List[str]:
        """Default symbol list as fallback"""
        return [
            'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'AVAX', 'UNI', 'ATOM', 'XRP',
            'LTC', 'BCH', 'XLM', 'VET', 'FIL', 'ALGO', 'AAVE', 'CAKE', 'THETA', 'TRX'
        ]

    def rate_limit(self):
        """Enforce rate limiting for API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def get_coin_id_for_symbol(self, symbol: str) -> Optional[str]:
        """Get CoinGecko coin_id for symbol"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT coin_id 
                FROM price_data_real 
                WHERE symbol = %s 
                AND coin_id IS NOT NULL 
                AND coin_id != ''
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else symbol.lower()
            
        except Exception as e:
            logger.error(f"❌ Error getting coin_id for {symbol}: {e}")
            return symbol.lower()

    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self.rate_limit()
        self.stats['api_calls_made'] += 1
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed for {endpoint}: {e}")
            self.health_metrics['api_error_count'] += 1
            return None

    def collect_ohlc_for_symbol(self, symbol: str) -> int:
        """Collect OHLC data for a specific symbol"""
        try:
            coin_id = self.get_coin_id_for_symbol(symbol)
            
            # Get OHLC data for the last 7 days (hourly granularity)
            endpoint = f"coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': 7
            }
            
            logger.debug(f"📈 Collecting OHLC data for {symbol} ({coin_id})...")
            ohlc_data = self.make_request(endpoint, params)
            
            if not ohlc_data:
                logger.warning(f"⚠️ No OHLC data for {symbol}")
                return 0
            
            # Get current 24h volume data
            volume = self.get_current_volume(coin_id)
            
            return self.store_ohlc_data(symbol, coin_id, ohlc_data, volume)
            
        except Exception as e:
            logger.error(f"❌ Error collecting OHLC for {symbol}: {e}")
            return 0

    def get_current_volume(self, coin_id: str) -> Optional[float]:
        """Get current 24h volume for a coin"""
        try:
            endpoint = f"coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false', 
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            data = self.make_request(endpoint, params)
            
            if data and 'market_data' in data and 'total_volume' in data['market_data']:
                volume_usd = data['market_data']['total_volume'].get('usd', 0)
                return float(volume_usd) if volume_usd else None
                
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ Could not fetch volume for {coin_id}: {e}")
            return None

    def store_ohlc_data(self, symbol: str, coin_id: str, ohlc_data: List, volume: Optional[float] = None) -> int:
        """Store OHLC data in database with optional volume data"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            insert_sql = """
                INSERT INTO ohlc_data 
                (symbol, coin_id, timestamp_unix, timestamp_iso, 
                 open_price, high_price, low_price, close_price, volume, data_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume),
                    data_source = VALUES(data_source)
            """
            
            records_inserted = 0
            
            for ohlc in ohlc_data:
                if len(ohlc) >= 5:
                    timestamp_unix = int(ohlc[0])
                    timestamp_iso = datetime.fromtimestamp(timestamp_unix / 1000)
                    
                    # Use provided volume or try to extract from OHLC array (if available)
                    record_volume = volume
                    if record_volume is None and len(ohlc) > 5:
                        record_volume = float(ohlc[5])
                    
                    values = (
                        symbol,
                        coin_id,
                        timestamp_unix,
                        timestamp_iso,
                        float(ohlc[1]),  # open
                        float(ohlc[2]),  # high
                        float(ohlc[3]),  # low
                        float(ohlc[4]),  # close
                        record_volume,   # volume from parameter or OHLC array
                        'enhanced_ohlc_collector'
                    )
                    
                    cursor.execute(insert_sql, values)
                    records_inserted += 1
            
            conn.commit()
            conn.close()
            
            self.stats['database_writes'] += 1
            self.stats['ohlc_records_collected'] += records_inserted
            
            volume_info = f" with volume ${volume:,.0f}" if volume else " (no volume data)"
            logger.debug(f"   ✅ Stored {records_inserted} OHLC records for {symbol}{volume_info}")
            return records_inserted
            
        except Exception as e:
            logger.error(f"❌ Error storing OHLC data for {symbol}: {e}")
            self.health_metrics['database_error_count'] += 1
            return 0

    def collect_all_ohlc_data(self) -> Dict[str, Any]:
        """Collect OHLC data for all symbols"""
        start_time = datetime.now()
        self.stats['total_collections'] += 1
        self.stats['last_collection'] = start_time.isoformat()
        
        logger.info(f"🔄 Starting OHLC collection for {len(self.symbols)} symbols...")
        
        total_records = 0
        successful_symbols = 0
        failed_symbols = 0
        
        for symbol in self.symbols:
            try:
                records = self.collect_ohlc_for_symbol(symbol)
                if records > 0:
                    total_records += records
                    successful_symbols += 1
                    self.health_metrics['consecutive_failures'] = 0
                else:
                    failed_symbols += 1
                    self.health_metrics['consecutive_failures'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {symbol}: {e}")
                failed_symbols += 1
                self.health_metrics['consecutive_failures'] += 1
        
        # Update statistics
        duration = (datetime.now() - start_time).total_seconds()
        self.stats['symbols_processed'] = successful_symbols
        
        if successful_symbols > 0:
            self.stats['successful_collections'] += 1
            self.stats['last_success'] = datetime.now().isoformat()
        else:
            self.stats['failed_collections'] += 1
            self.stats['last_error'] = datetime.now().isoformat()
        
        result = {
            'status': 'completed',
            'duration_seconds': duration,
            'symbols_processed': len(self.symbols),
            'successful_symbols': successful_symbols,
            'failed_symbols': failed_symbols,
            'total_records_collected': total_records,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ OHLC collection completed: {successful_symbols}/{len(self.symbols)} symbols, {total_records} records")
        return result

    def detect_data_gap(self) -> Optional[int]:
        """Detect gaps in OHLC data collection"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TIMESTAMPDIFF(HOUR, MAX(timestamp_iso), NOW()) as hours_gap
                FROM ohlc_data 
                WHERE data_source = 'enhanced_ohlc_collector'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else 0
            
        except Exception as e:
            logger.error(f"❌ Error detecting data gap: {e}")
            return None

    def calculate_health_score(self) -> int:
        """Calculate service health score (0-100)"""
        score = 100
        
        # Data freshness (40 points)
        gap_hours = self.detect_data_gap() or 0
        if gap_hours > 24:
            score -= 40
        elif gap_hours > 6:
            score -= 20
        elif gap_hours > 2:
            score -= 10
        
        # Collection success rate (30 points)
        total_collections = self.stats['total_collections']
        if total_collections > 0:
            success_rate = self.stats['successful_collections'] / total_collections
            score -= int((1 - success_rate) * 30)
        
        # Error rates (20 points)
        if self.health_metrics['consecutive_failures'] > 5:
            score -= 20
        elif self.health_metrics['consecutive_failures'] > 2:
            score -= 10
        
        # API availability (10 points)
        if self.health_metrics['api_error_count'] > 10:
            score -= 10
        elif self.health_metrics['api_error_count'] > 5:
            score -= 5
        
        return max(0, min(100, score))

    def _setup_api_endpoints(self):
        """Setup FastAPI endpoints matching template standard"""
        
        @self.app.get("/health")
        def health_check():
            """Health check endpoint"""
            gap_hours = self.detect_data_gap()
            health_score = self.calculate_health_score()
            
            return {
                "status": "healthy" if health_score > 70 else "degraded",
                "health_score": health_score,
                "service": self.service_name,
                "gap_hours": gap_hours,
                "data_freshness": "healthy" if (gap_hours or 0) < 2 else "stale",
                "symbols_tracked": len(self.symbols),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/status")
        def get_status():
            """Detailed operational status"""
            gap_hours = self.detect_data_gap()
            health_score = self.calculate_health_score()
            uptime = datetime.now() - self.health_metrics['service_start_time']
            
            return {
                "service": self.service_name,
                "status": "operational" if health_score > 50 else "degraded",
                "uptime_seconds": int(uptime.total_seconds()),
                "statistics": self.stats,
                "configuration": {
                    "symbols_tracked": len(self.symbols),
                    "collection_interval": self.collection_interval,
                    "api_key_configured": bool(self.api_key),
                    "database_connected": True  # TODO: Add actual connection check
                },
                "health_metrics": {
                    "gap_hours": gap_hours,
                    "health_score": health_score,
                    "consecutive_failures": self.health_metrics['consecutive_failures'],
                    "api_error_count": self.health_metrics['api_error_count'],
                    "database_error_count": self.health_metrics['database_error_count']
                }
            }

        @self.app.post("/collect")
        async def trigger_collection(background_tasks: BackgroundTasks):
            """Trigger manual OHLC data collection"""
            background_tasks.add_task(self.collect_all_ohlc_data)
            return {
                "status": "started",
                "message": "OHLC data collection triggered",
                "symbols_to_process": len(self.symbols),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and optionally auto-backfill"""
            gap_hours = self.detect_data_gap()
            health_score = self.calculate_health_score()
            
            backfill_triggered = False
            if gap_hours and 2 < gap_hours < 48:
                try:
                    self.collect_all_ohlc_data()
                    backfill_triggered = True
                except Exception as e:
                    logger.error(f"Auto-backfill failed: {e}")
            
            return {
                "status": "completed",
                "gap_hours": gap_hours,
                "health_score": health_score,
                "backfill_triggered": backfill_triggered,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/backfill/{hours}")
        def manual_backfill(hours: int, background_tasks: BackgroundTasks):
            """Manually trigger intensive OHLC data collection"""
            if hours > 168:  # Max 1 week
                return {"error": "Maximum backfill period is 168 hours (1 week)"}
            
            background_tasks.add_task(self._intensive_backfill, hours)
            return {
                "status": "started", 
                "message": f"Intensive OHLC collection initiated for {hours} hours",
                "estimated_collections": max(1, hours // 6),  # Every 6 hours
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            gap_hours = self.detect_data_gap() or 0
            health_score = self.calculate_health_score()
            
            metrics_text = f"""# HELP ohlc_collector_total_collected Total OHLC records collected
# TYPE ohlc_collector_total_collected counter
ohlc_collector_total_collected {self.stats['ohlc_records_collected']}

# HELP ohlc_collector_collection_errors Total collection errors
# TYPE ohlc_collector_collection_errors counter
ohlc_collector_collection_errors {self.stats['failed_collections']}

# HELP ohlc_collector_symbols_tracked Number of symbols tracked
# TYPE ohlc_collector_symbols_tracked gauge
ohlc_collector_symbols_tracked {len(self.symbols)}

# HELP ohlc_collector_health_score Service health score (0-100)
# TYPE ohlc_collector_health_score gauge
ohlc_collector_health_score {health_score}

# HELP ohlc_collector_gap_hours Data gap in hours
# TYPE ohlc_collector_gap_hours gauge
ohlc_collector_gap_hours {gap_hours}

# HELP ohlc_collector_api_calls_made Total API calls made
# TYPE ohlc_collector_api_calls_made counter
ohlc_collector_api_calls_made {self.stats['api_calls_made']}

# HELP ohlc_collector_database_writes Total database writes
# TYPE ohlc_collector_database_writes counter
ohlc_collector_database_writes {self.stats['database_writes']}

# HELP ohlc_collector_running Service running status
# TYPE ohlc_collector_running gauge
ohlc_collector_running 1
"""
            return PlainTextResponse(metrics_text, media_type="text/plain")
        
        @self.app.get("/ohlc-features")
        def ohlc_features():
            """OHLC data feature information"""
            return {
                "data_source": "CoinGecko Premium API",
                "ohlc_components": {
                    "Open": "Opening price for the time period",
                    "High": "Highest price during the time period",
                    "Low": "Lowest price during the time period", 
                    "Close": "Closing price for the time period",
                    "Volume": "Trading volume during the time period"
                },
                "ml_applications": {
                    "candlestick_patterns": "Technical analysis pattern recognition",
                    "volatility_analysis": "High-Low range calculations",
                    "price_momentum": "Open to close price movements",
                    "volume_analysis": "Trading activity correlation",
                    "market_microstructure": "Intraday price behavior"
                },
                "tracked_symbols": len(self.symbols),
                "collection_frequency": "Every 1 hour",
                "data_retention": "Up to 7 days per collection cycle",
                "api_source": "CoinGecko Premium OHLC endpoint",
                "rate_limits": "500 calls/minute (Premium tier)"
            }

    def _intensive_backfill(self, hours: int):
        """Run intensive backfill for specified hours"""
        logger.info(f"Starting intensive OHLC backfill for {hours} hours")
        
        # Run multiple collection cycles
        cycles = min(hours // 6, 12)  # Every 6 hours, max 12 cycles
        for i in range(cycles):
            try:
                result = self.collect_all_ohlc_data()
                logger.info(f"Backfill cycle {i+1}/{cycles} completed: {result.get('total_records_collected', 0)} records")
                if i < cycles - 1:  # Don't sleep after last cycle
                    time.sleep(300)  # 5 minute break between cycles
            except Exception as e:
                logger.error(f"Backfill cycle {i+1} failed: {e}")

    def run_service(self, host: str = "0.0.0.0", port: int = 8002):
        """Run the FastAPI service"""
        logger.info(f"🚀 Starting {self.service_name} on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")

    def run_scheduler(self):
        """Run scheduled collection (alternative to FastAPI service)"""
        logger.info(f"🕒 Starting scheduled OHLC collection every {self.collection_interval} seconds")
        
        # Schedule regular collection
        schedule.every(self.collection_interval).seconds.do(self.collect_all_ohlc_data)
        
        # Run initial collection
        self.collect_all_ohlc_data()
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced OHLC Collector")
    parser.add_argument("--mode", choices=["api", "scheduler"], default="api",
                        help="Run mode: 'api' for FastAPI service, 'scheduler' for scheduled collection")
    parser.add_argument("--host", default="0.0.0.0", help="API host (api mode only)")
    parser.add_argument("--port", type=int, default=8002, help="API port (api mode only)")
    
    args = parser.parse_args()
    
    collector = EnhancedOHLCCollector()
    
    try:
        if args.mode == "api":
            collector.run_service(host=args.host, port=args.port)
        else:
            collector.run_scheduler()
    except KeyboardInterrupt:
        logger.info("⚠️ Service interrupted by user")
    except Exception as e:
        logger.error(f"❌ Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()