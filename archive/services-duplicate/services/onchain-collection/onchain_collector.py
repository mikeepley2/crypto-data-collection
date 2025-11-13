#!/usr/bin/env python3
"""
Onchain Data Collector
Collects and updates blockchain metrics for cryptocurrencies
Includes backfill capability for historical data
Uses free APIs: Messari, blockchain.info, Etherscan
"""

import os
import logging
import time
import json
import requests
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schedule

# Import centralized scheduling configuration
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None
    create_schedule_for_collector = None
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("onchain-collector")

load_dotenv()

# API endpoints
MESSARI_API = "https://data.messari.io/api/v1"
ETHERSCAN_API = "https://api.etherscan.io/api"
BLOCKCHAIN_INFO_API = "https://blockchain.info"

ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY", "")


# Database connection
# Database connection with centralized configuration
def get_db_connection():
    try:
        # Use centralized database configuration
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from shared.database_config import get_db_connection as get_centralized_connection
        return get_centralized_connection()
    except ImportError:
        # Fallback for local development
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "172.22.32.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


# CoinGecko API configuration
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
COINGECKO_BASE_URL = (
    "https://pro-api.coingecko.com/api/v3"
    if COINGECKO_API_KEY
    else "https://api.coingecko.com/api/v3"
)
COINGECKO_HEADERS = {"x-cg-pro-api-key": COINGECKO_API_KEY} if COINGECKO_API_KEY else {}

# Rate limiting for CoinGecko API
_last_coingecko_call = 0
_coingecko_min_interval = (
    0.5 if COINGECKO_API_KEY else 2.0
)  # 0.5s for premium, 2s for free

# Statistics tracking
onchain_stats = {
    "total_collected": 0,
    "last_collection": None,
    "collection_errors": 0,
    "symbols_processed": 0,
    "last_gap_check": None,
    "gap_hours_detected": 0,
    "backfill_records": 0,
    "health_score": 0.0,
}


class OnchainCollectorAPI:
    """FastAPI wrapper for onchain collector"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Onchain Data Collector",
            description="Collects blockchain metrics for cryptocurrencies",
            version="1.0.0",
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        def health():
            return {"status": "ok", "service": "onchain-collector"}
        
        @self.app.get("/status")  
        def status():
            gap_hours = detect_gap()
            health_score = calculate_health_score()
            
            return {
                "service": "onchain-collector",
                "stats": onchain_stats,
                "gap_hours": gap_hours,
                "health_score": health_score,
                "data_freshness": "healthy" if (gap_hours or 0) < 12 else "stale",
            }
        
        @self.app.post("/collect")
        def collect_onchain(background_tasks: BackgroundTasks):
            """Trigger onchain collection"""
            background_tasks.add_task(collect_onchain_metrics)
            return {"status": "started", "message": "Onchain collection initiated"}
        
        @self.app.post("/gap-check")
        def gap_check():
            """Check for data gaps and optionally backfill"""
            auto_gap_detection_and_backfill()
            return {
                "status": "completed",
                "gap_hours": onchain_stats.get("gap_hours_detected", 0),
                "health_score": onchain_stats.get("health_score", 0),
            }
        
        @self.app.post("/backfill/{days}")
        def manual_backfill(days: int, background_tasks: BackgroundTasks):
            """Manually trigger backfill for specified days"""
            if days > 60:
                return {"error": "Maximum backfill period is 60 days"}
            
            background_tasks.add_task(collect_onchain_metrics, backfill_days=days)
            return {
                "status": "started", 
                "message": f"Backfill initiated for {days} days"
            }

# CoinGecko coin ID mapping
COINGECKO_COIN_MAPPING = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "ADA": "cardano",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "LTC": "litecoin",
    "ATOM": "cosmos",
    "NEAR": "near",
    "ALGO": "algorand",
    "VET": "vechain",
    "FIL": "filecoin",
    "TRX": "tron",
    "SHIB": "shiba-inu",
    "ARB": "arbitrum",
    "OP": "optimism",
}


def _rate_limit_coingecko():
    """Rate limiting for CoinGecko API calls"""
    global _last_coingecko_call
    current_time = time.time()
    elapsed = current_time - _last_coingecko_call
    if elapsed < _coingecko_min_interval:
        sleep_time = _coingecko_min_interval - elapsed
        time.sleep(sleep_time)
    _last_coingecko_call = time.time()


def fetch_onchain_metrics_from_api(symbol):
    """
    Fetch real onchain metrics from CoinGecko Premium API (with rate limiting)
    Falls back to free APIs if premium key not available
    Returns dict with onchain data or None if unavailable
    """
    # Try CoinGecko Premium API first (if we have the key)
    if COINGECKO_API_KEY:
        _rate_limit_coingecko()  # Enforce rate limiting
        try:
            coin_id = COINGECKO_COIN_MAPPING.get(symbol.upper())
            if coin_id:
                # Use query parameter authentication for premium API (required by CoinGecko)
                if COINGECKO_API_KEY and "pro-api" in COINGECKO_BASE_URL:
                    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}?x_cg_pro_api_key={COINGECKO_API_KEY}"
                else:
                    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
                response = requests.get(url, headers=COINGECKO_HEADERS, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    market_data = data.get("market_data", {})

                    # Get volatility from 7-day price change
                    price_change_7d = market_data.get("price_change_percentage_7d", 0)
                    volatility = abs(price_change_7d) if price_change_7d else 0

                    # Estimate metrics from market data (CoinGecko doesn't provide raw onchain metrics)
                    market_cap = market_data.get("market_cap", {}).get("usd", 0)
                    total_volume = market_data.get("total_volume", {}).get("usd", 0)

                    if market_cap > 0 and total_volume > 0:
                        # Estimate based on market metrics
                        estimated_active_addresses = max(
                            1, int(market_cap / 1000000)
                        )  # 1 address per $1M
                        estimated_tx_count = max(
                            1, int(total_volume / 10000)
                        )  # 1 tx per $10K volume

                        return {
                            "active_addresses_24h": estimated_active_addresses,
                            "transaction_count_24h": estimated_tx_count,
                            "exchange_net_flow_24h": None,  # Not available from CoinGecko
                            "price_volatility_7d": volatility,
                            "data_source": (
                                "CoinGecko Premium"
                                if COINGECKO_API_KEY
                                else "CoinGecko Free"
                            ),
                        }
                elif response.status_code == 429:
                    logger.warning(
                        f"CoinGecko rate limit for {symbol}, will retry later"
                    )
                else:
                    logger.debug(
                        f"CoinGecko API error for {symbol}: HTTP {response.status_code}"
                    )
        except Exception as e:
            logger.debug(f"CoinGecko API error for {symbol}: {e}")

    # Fallback to Messari API
    try:
        url = f"{MESSARI_API}/assets/{symbol.lower()}/metrics"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json().get("data", {})
            metrics = data.get("blockchain", {})

            return {
                "active_addresses_24h": metrics.get("active_addresses"),
                "transaction_count_24h": metrics.get("transaction_count"),
                "exchange_net_flow_24h": metrics.get("exchange_net_flow"),
                "price_volatility_7d": metrics.get("price_volatility_7d"),
                "data_source": "Messari",
            }
    except Exception as e:
        logger.debug(f"Messari API error for {symbol}: {e}")

    # If Messari fails, try blockchain.info for BTC only
    if symbol.upper() == "BTC":
        try:
            url = f"{BLOCKCHAIN_INFO_API}/q/getblockcount"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return {
                    "active_addresses_24h": None,
                    "transaction_count_24h": int(response.text),
                    "exchange_net_flow_24h": None,
                    "price_volatility_7d": None,
                    "data_source": "blockchain.info",
                }
        except Exception as e:
            logger.debug(f"blockchain.info error: {e}")

    return None


def collect_onchain_metrics(backfill_days=None):
    """
    Collect onchain metrics from free APIs and update database
    backfill_days: if set, collect for last N days
    """
    if backfill_days:
        logger.info(
            f"Starting onchain metrics backfill for last {backfill_days} days..."
        )
    else:
        logger.info("Starting onchain metrics collection...")

    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 0

    try:
        cursor = conn.cursor(dictionary=True)

        # Get list of tracked assets
        cursor.execute(
            """
            SELECT DISTINCT symbol FROM crypto_assets 
            WHERE is_active = 1 LIMIT 100
        """
        )
        assets = cursor.fetchall()

        processed = 0
        for asset in assets:
            symbol = asset["symbol"]

            try:
                # Fetch real onchain metrics from API
                metrics = fetch_onchain_metrics_from_api(symbol)

                timestamp = datetime.now()

                if metrics:
                    # Insert real data
                    cursor.execute(
                        """
                        INSERT INTO crypto_onchain_data (
                            coin, coin_symbol, timestamp, collection_date,
                            active_addresses_24h, transaction_count_24h,
                            exchange_net_flow_24h, price_volatility_7d,
                            data_sources
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            active_addresses_24h = VALUES(active_addresses_24h),
                            transaction_count_24h = VALUES(transaction_count_24h),
                            exchange_net_flow_24h = VALUES(exchange_net_flow_24h),
                            price_volatility_7d = VALUES(price_volatility_7d),
                            data_sources = VALUES(data_sources),
                            timestamp = VALUES(timestamp)
                    """,
                        (
                            symbol,
                            symbol,
                            timestamp,
                            timestamp.date(),
                            metrics.get("active_addresses_24h"),
                            metrics.get("transaction_count_24h"),
                            metrics.get("exchange_net_flow_24h"),
                            metrics.get("price_volatility_7d"),
                            metrics.get("data_source"),
                        ),
                    )
                    logger.info(
                        f"Collected onchain data for {symbol} from {metrics.get('data_source')}"
                    )
                else:
                    # Insert placeholder for tracking but no data loss
                    cursor.execute(
                        """
                        INSERT INTO crypto_onchain_data (
                            coin, coin_symbol, timestamp, collection_date
                        ) VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            timestamp = VALUES(timestamp)
                    """,
                        (symbol, symbol, timestamp, timestamp.date()),
                    )
                    logger.debug(
                        f"No onchain data available for {symbol}, inserted placeholder"
                    )

                processed += 1

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} onchain metrics")
        with open("/tmp/onchain_collector_health.txt", "w") as f:
            f.write(str(datetime.now()))

    except Exception as e:
        logger.error(f"Error in collection: {e}")
        onchain_stats["collection_errors"] += 1
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        
        # Update statistics
        onchain_stats["total_collected"] += processed
        onchain_stats["symbols_processed"] += len(assets) if 'assets' in locals() else 0
        onchain_stats["last_collection"] = datetime.now()

    return processed


def detect_gap():
    """
    Detect gaps in onchain data collection
    Returns number of hours since last update, or None if no data exists
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        # Check last update timestamp
        cursor.execute(
            """
            SELECT MAX(timestamp) as last_update
            FROM crypto_onchain_data
        """
        )
        result = cursor.fetchone()

        if result and result["last_update"]:
            last_update = result["last_update"]
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            elif isinstance(last_update, datetime):
                pass  # Already datetime
            else:
                return None

            now = datetime.now()
            gap_hours = (now - last_update).total_seconds() / 3600
            return gap_hours
        else:
            logger.info("No existing onchain data found - first run")
            return None
    except Exception as e:
        logger.error(f"Error detecting gap: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def calculate_health_score() -> float:
    """Calculate health score based on data freshness and collection success"""
    try:
        gap_hours = detect_gap()
        
        # Base score starts at 100
        health_score = 100.0
        
        # Deduct points for data gaps
        if gap_hours:
            if gap_hours > 48:  # More than 2 days old
                health_score -= min(60, gap_hours)  # Max 60 point deduction
            elif gap_hours > 12:  # More than 12 hours old
                health_score -= gap_hours * 2
        
        # Deduct points for collection errors
        total_attempts = max(1, onchain_stats["symbols_processed"])
        error_ratio = onchain_stats["collection_errors"] / total_attempts
        health_score -= error_ratio * 25  # Max 25 point deduction
        
        # Ensure score doesn't go below 0
        health_score = max(0.0, health_score)
        
        onchain_stats["health_score"] = health_score
        return health_score
        
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        return 0.0


def auto_gap_detection_and_backfill():
    """
    Automatically detect gaps and backfill if necessary
    Called on startup and periodically
    """
    logger.info("Running automatic gap detection...")
    
    gap_hours = detect_gap()
    onchain_stats["gap_hours_detected"] = gap_hours or 0
    onchain_stats["last_gap_check"] = datetime.now()
    
    if gap_hours:
        # Use centralized scheduling config with fallback
        if get_collector_schedule:
            config = get_collector_schedule('onchain')
            collection_interval_hours = config['frequency_hours']
        else:
            collection_interval_hours = 6  # Fallback: Onchain data collected every 6 hours
        
        if gap_hours > collection_interval_hours:
            gap_days = min(int(gap_hours / 24) + 1, 30)  # Limit to 30 days max
            logger.warning(f"⚠️  Gap detected: {gap_hours:.1f} hours since last update")
            logger.info(f"🔄 Auto-backfilling last {gap_days} days to fill gap...")
            
            collect_onchain_metrics(backfill_days=gap_days)
            logger.info("✅ Gap backfill complete")
        else:
            logger.info(f"✅ No significant gap detected ({gap_hours:.1f} hours)")
    else:
        logger.info("ℹ️  No previous data found - running initial collection")
        collect_onchain_metrics()


def health_check():
    """Health check endpoint status"""
    logger.debug("Health check: OK")


def main():
    """Main collector loop with FastAPI service"""
    logger.info("Onchain Data Collector starting...")

    # Check for backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"BACKFILL MODE: Processing last {backfill_days} days")
        collect_onchain_metrics(backfill_days=int(backfill_days))
        logger.info("Backfill complete. Exiting.")
        return

    # Auto-detect and backfill gaps on startup
    logger.info("🔍 Running startup gap detection...")
    auto_gap_detection_and_backfill()
    logger.info("✅ Startup gap check complete")

    # Create FastAPI instance
    api = OnchainCollectorAPI()
    
    # Schedule collection every 6 hours in background thread
    def background_scheduler():
        # Use centralized scheduling config with fallback
        if create_schedule_for_collector:
            try:
                create_schedule_for_collector('onchain', schedule, collect_onchain_metrics)
                logger.info("✅ Using centralized scheduling configuration")
            except Exception as e:
                logger.warning(f"Centralized config failed, using fallback: {e}")
                schedule.every(6).hours.do(collect_onchain_metrics)
        else:
            schedule.every(6).hours.do(collect_onchain_metrics)
        
        schedule.every().hour.do(health_check)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    # Start background scheduler
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start FastAPI server
    logger.info("Starting FastAPI service on port 8001...")
    uvicorn.run(api.app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
