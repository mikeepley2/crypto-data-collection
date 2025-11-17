#!/usr/bin/env python3
"""
Onchain Data Collector - Free Version
Collects blockchain metrics without paid APIs
Uses free sources: Etherscan, blockchain.info, API.tokenmetrics.com, etc.
"""

import os
import logging
import time
import requests
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schedule
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("onchain-collector")
load_dotenv()

# Free API endpoints
ETHERSCAN_API = "https://api.etherscan.io/api"
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY", "YourEtherscanAPIKey")  # Free tier available
BLOCKCHAIN_INFO_API = "https://blockchain.info"
GLASSNODE_SAMPLE = "https://data.messari.io/api/v1"  # Messari has free tier

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


def get_bitcoin_data():
    """Get Bitcoin onchain data from blockchain.info"""
    try:
        url = f"{BLOCKCHAIN_INFO_API}/q/getblockcount"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            blocks = int(response.text)
            logger.info(f"Bitcoin blocks: {blocks}")
            return {"blocks": blocks}
    except Exception as e:
        logger.error(f"Error getting Bitcoin data: {e}")
    return None


def get_ethereum_data():
    """Get Ethereum onchain data from Etherscan API"""
    try:
        # Get Ethereum network stats
        params = {
            "module": "stats",
            "action": "ethsupply",
            "apikey": ETHERSCAN_KEY
        }
        response = requests.get(ETHERSCAN_API, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                eth_supply = int(data.get("result", 0)) / 1e18
                logger.info(f"Ethereum supply: {eth_supply:.2f}")
                return {"eth_supply": eth_supply}
    except Exception as e:
        logger.error(f"Error getting Ethereum data: {e}")
    return None


def get_general_crypto_metrics():
    """Get general crypto metrics from Messari free API"""
    try:
        # Messari free API endpoint - Bitcoin metrics
        url = "https://data.messari.io/api/v1/assets/bitcoin/metrics"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            metrics = data.get("data", {}).get("market_data", {})
            return {
                "market_cap": metrics.get("market_cap"),
                "volume_24h": metrics.get("volume_last_24_hours"),
            }
    except Exception as e:
        logger.error(f"Error getting crypto metrics: {e}")
    return None


def collect_onchain_metrics():
    """Collect onchain metrics from free sources"""
    logger.info("Starting FREE onchain metrics collection...")
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return

    try:
        cursor = conn.cursor(dictionary=True)
        timestamp = datetime.utcnow()
        processed = 0

        # Get data for major cryptocurrencies
        symbols_data = {
            "BTC": {"source": "blockchain.info", "data": get_bitcoin_data()},
            "ETH": {"source": "etherscan", "data": get_ethereum_data()},
        }

        # Get top 50 active symbols from database
        cursor.execute("SELECT DISTINCT symbol FROM crypto_assets WHERE active = 1 LIMIT 50")
        assets = cursor.fetchall()

        for asset in assets:
            symbol = asset["symbol"]
            try:
                # Use general metrics for most coins
                metrics = get_general_crypto_metrics() if symbol in ["BTC", "ETH"] else {}
                
                if metrics:
                    cursor.execute(
                        """INSERT INTO onchain_metrics (
                            symbol, timestamp, active_addresses, transaction_count,
                            transaction_volume, miner_revenue, exchange_inflow, exchange_outflow
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            active_addresses = VALUES(active_addresses),
                            transaction_count = VALUES(transaction_count),
                            transaction_volume = VALUES(transaction_volume),
                            miner_revenue = VALUES(miner_revenue),
                            exchange_inflow = VALUES(exchange_inflow),
                            exchange_outflow = VALUES(exchange_outflow),
                            updated_at = NOW()""",
                        (
                            symbol, timestamp,
                            metrics.get("active_addresses"),
                            metrics.get("transaction_count"),
                            metrics.get("transaction_volume"),
                            metrics.get("miner_revenue"),
                            metrics.get("exchange_inflow"),
                            metrics.get("exchange_outflow"),
                        ),
                    )
                    processed += 1
                else:
                    # Insert placeholder data for symbols without specific metrics
                    cursor.execute(
                        """INSERT INTO onchain_metrics (
                            symbol, timestamp, active_addresses, transaction_count,
                            transaction_volume, miner_revenue, exchange_inflow, exchange_outflow
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            active_addresses = VALUES(active_addresses),
                            transaction_count = VALUES(transaction_count),
                            transaction_volume = VALUES(transaction_volume),
                            miner_revenue = VALUES(miner_revenue),
                            exchange_inflow = VALUES(exchange_inflow),
                            exchange_outflow = VALUES(exchange_outflow),
                            updated_at = NOW()""",
                        (symbol, timestamp, None, None, None, None, None, None),
                    )
                    processed += 1
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} onchain metrics from FREE sources")
        with open("/tmp/onchain_collector_health.txt", "w") as f:
            f.write(str(datetime.utcnow()))
    except Exception as e:
        logger.error(f"Error in collection: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def main():
    logger.info("Onchain Data Collector (FREE) starting...")
    logger.info("Using free data sources: blockchain.info, etherscan, messari")
    
    schedule.every(6).hours.do(collect_onchain_metrics)
    collect_onchain_metrics()
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
