#!/usr/bin/env python3
"""
Macro Indicators Collector
Collects and updates macroeconomic indicators from FRED API
Includes backfill capability for historical data
"""

import os
import logging
import time
import mysql.connector
from datetime import datetime, timedelta
import schedule
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("macro-collector")

# FRED API endpoint and configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Mapping of indicator names to FRED series IDs
FRED_SERIES = {
    "US_UNEMPLOYMENT": "UNRATE",           # Unemployment Rate
    "US_INFLATION": "CPIAUCSL",            # Consumer Price Index
    "US_GDP": "A191RO1Q156NBEA",           # Real GDP
    "FEDERAL_FUNDS_RATE": "FEDFUNDS",      # Federal Funds Rate
    "10Y_YIELD": "DFF10",                  # 10-Year Treasury Yield
    "VIX": "VIXCLS",                       # VIX Index
    "DXY": "DEXUSEU",                      # Dollar Index
    "GOLD_PRICE": "GOLDAMND",              # Gold Price
    "OIL_PRICE": "DCOILWTICO",             # Oil Price
}


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


def fetch_fred_data(series_id, backfill_days=None):
    """
    Fetch data from FRED API
    backfill_days: if set, fetch last N days
    """
    if not FRED_API_KEY:
        logger.warning("FRED_API_KEY not configured, using placeholder data")
        return None

    try:
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
        }

        if backfill_days:
            start_date = (datetime.now() - timedelta(days=backfill_days)).strftime(
                "%Y-%m-%d"
            )
            params["observation_start"] = start_date

        response = requests.get(
            f"{FRED_API_BASE}/series/observations", params=params, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            observations = data.get("observations", [])
            if observations:
                latest = observations[-1]  # Most recent observation
                try:
                    value = float(latest.get("value"))
                    return value
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse value for {series_id}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching FRED data for {series_id}: {e}")

    return None


def collect_macro_indicators(backfill_days=None):
    """
    Collect macroeconomic indicators
    backfill_days: if set, backfill last N days instead of just recent
    """
    if backfill_days:
        logger.info(f"Starting macro indicators backfill for last {backfill_days} days...")
    else:
        logger.info("Starting macro indicators collection...")

    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()

        timestamp = datetime.utcnow()
        processed = 0

        for indicator_name, series_id in FRED_SERIES.items():
            try:
                # Fetch real data from FRED if API key available
                value = fetch_fred_data(series_id, backfill_days)

                # Insert into database
                cursor.execute(
                    """
                    INSERT INTO macro_indicators (
                        indicator_name, indicator_date, value, data_source
                    ) VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        value = VALUES(value),
                        updated_at = NOW()
                """,
                    (indicator_name, timestamp.date(), value, "FRED API"),
                )
                processed += 1
                logger.info(
                    f"Collected {indicator_name}: {value if value is not None else 'N/A'}"
                )

            except Exception as e:
                logger.error(f"Error for {indicator_name}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} macro indicators")
        with open("/tmp/macro_collector_health.txt", "w") as f:
            f.write(str(datetime.utcnow()))

    except Exception as e:
        logger.error(f"Collection error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return processed


def main():
    logger.info("Macro Indicators Collector starting...")

    # Check for backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"BACKFILL MODE: Processing last {backfill_days} days")
        collect_macro_indicators(backfill_days=int(backfill_days))
        logger.info("Backfill complete. Exiting.")
        return

    # Normal operation: schedule every 1 hour
    schedule.every(1).hours.do(collect_macro_indicators)
    collect_macro_indicators()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
