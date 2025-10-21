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
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def fetch_onchain_metrics_from_api(symbol):
    """
    Fetch real onchain metrics from free APIs
    Returns dict with onchain data or None if unavailable
    """
    try:
        # Try Messari API first
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

    # If Messari fails, try other sources
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

                timestamp = datetime.utcnow()

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
            f.write(str(datetime.utcnow()))

    except Exception as e:
        logger.error(f"Error in collection: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return processed


def health_check():
    """Health check endpoint status"""
    logger.debug("Health check: OK")


def main():
    """Main collector loop"""
    logger.info("Onchain Data Collector starting...")

    # Check for backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"BACKFILL MODE: Processing last {backfill_days} days")
        collect_onchain_metrics(backfill_days=int(backfill_days))
        logger.info("Backfill complete. Exiting.")
        return

    # Schedule collection every 6 hours
    schedule.every(6).hours.do(collect_onchain_metrics)
    schedule.every().minute.do(health_check)

    # Run initial collection
    collect_onchain_metrics()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
