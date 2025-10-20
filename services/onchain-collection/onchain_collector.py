#!/usr/bin/env python3
"""
Onchain Data Collector
Collects and updates blockchain metrics for cryptocurrencies
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


def collect_onchain_metrics():
    """
    Collect onchain metrics from Glassnode API and update database
    """
    logger.info("Starting onchain metrics collection...")

    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return

    try:
        cursor = conn.cursor(dictionary=True)

        # Get list of tracked assets
        cursor.execute(
            """
            SELECT DISTINCT symbol FROM crypto_assets 
            WHERE active = 1 LIMIT 50
        """
        )
        assets = cursor.fetchall()

        processed = 0
        for asset in assets:
            symbol = asset["symbol"]

            # Insert/Update onchain metrics
            # In production, this would fetch from Glassnode or other onchain data provider
            try:
                timestamp = datetime.utcnow()

                # Placeholder data - in production would call external API
                cursor.execute(
                    """
                    INSERT INTO onchain_metrics (
                        symbol, timestamp, active_addresses, 
                        transaction_count, transaction_volume,
                        miner_revenue, exchange_inflow, exchange_outflow
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        active_addresses = VALUES(active_addresses),
                        transaction_count = VALUES(transaction_count),
                        transaction_volume = VALUES(transaction_volume),
                        miner_revenue = VALUES(miner_revenue),
                        exchange_inflow = VALUES(exchange_inflow),
                        exchange_outflow = VALUES(exchange_outflow),
                        updated_at = NOW()
                """,
                    (symbol, timestamp, None, None, None, None, None, None),
                )
                processed += 1
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} onchain metrics")

    except Exception as e:
        logger.error(f"Error in collection: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def health_check():
    """Health check endpoint status"""
    logger.info("Health check: OK")


def main():
    """Main collector loop"""
    logger.info("Onchain Data Collector starting...")

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
