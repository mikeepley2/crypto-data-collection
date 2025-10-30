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
# FRED API key - check env var first, then use valid default from aitest folder
FRED_API_KEY = os.getenv("FRED_API_KEY", "35478996c5e061d0fc99fc73f5ce348d")

# Mapping of indicator names to FRED series IDs
FRED_SERIES = {
    "US_UNEMPLOYMENT": "UNRATE",  # Unemployment Rate
    "US_INFLATION": "CPIAUCSL",  # Consumer Price Index
    "US_GDP": "A191RO1Q156NBEA",  # Real GDP
    "FEDERAL_FUNDS_RATE": "FEDFUNDS",  # Federal Funds Rate
    "10Y_YIELD": "DFF10",  # 10-Year Treasury Yield
    "VIX": "VIXCLS",  # VIX Index
    "DXY": "DEXUSEU",  # Dollar Index
    "GOLD_PRICE": "GOLDAMND",  # Gold Price
    "OIL_PRICE": "DCOILWTICO",  # Oil Price
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
    Returns latest value if backfill_days is None, or all observations if backfill_days is set
    """
    if not FRED_API_KEY:
        logger.error("FRED_API_KEY not configured, cannot fetch data")
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
            f"{FRED_API_BASE}/series/observations", params=params, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            observations = data.get("observations", [])
            if observations:
                if backfill_days:
                    # Return all observations for backfill
                    results = []
                    for obs in observations:
                        try:
                            value = obs.get("value")
                            if (
                                value != "." and value is not None
                            ):  # FRED uses "." for missing
                                date_str = obs.get("date")
                                if date_str:
                                    results.append(
                                        {
                                            "date": datetime.strptime(
                                                date_str, "%Y-%m-%d"
                                            ).date(),
                                            "value": float(value),
                                        }
                                    )
                        except (ValueError, TypeError) as e:
                            logger.debug(
                                f"Could not parse observation for {series_id} on {obs.get('date')}: {e}"
                            )
                            continue
                    return results
                else:
                    # Return just latest value for normal collection
                    latest = observations[-1]
                    try:
                        value = latest.get("value")
                        if value != "." and value is not None:
                            return float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse value for {series_id}")
                        return None
        else:
            logger.error(f"FRED API error for {series_id}: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching FRED data for {series_id}: {e}")

    return None


def collect_macro_indicators(backfill_days=None):
    """
    Collect macroeconomic indicators
    backfill_days: if set, backfill last N days instead of just recent
    """
    if backfill_days:
        logger.info(
            f"Starting macro indicators backfill for last {backfill_days} days..."
        )
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
                data = fetch_fred_data(series_id, backfill_days)

                if data is None:
                    logger.warning(f"No data returned for {indicator_name}")
                    continue

                if backfill_days and isinstance(data, list):
                    # Backfill mode: insert all historical observations
                    for obs in data:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO macro_indicators (
                                    indicator_name, indicator_date, value, data_source
                                ) VALUES (%s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                    value = VALUES(value),
                                    updated_at = NOW()
                            """,
                                (indicator_name, obs["date"], obs["value"], "FRED API"),
                            )
                            processed += 1
                        except Exception as e:
                            logger.debug(
                                f"Error inserting {indicator_name} for {obs['date']}: {e}"
                            )
                    logger.info(
                        f"Backfilled {len(data)} observations for {indicator_name}"
                    )
                else:
                    # Normal mode: insert latest value
                    cursor.execute(
                        """
                        INSERT INTO macro_indicators (
                            indicator_name, indicator_date, value, data_source
                        ) VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            value = VALUES(value),
                            updated_at = NOW()
                    """,
                        (indicator_name, timestamp.date(), data, "FRED API"),
                    )
                    processed += 1
                    logger.info(
                        f"Collected {indicator_name}: {data if data is not None else 'N/A'}"
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


def detect_gap():
    """
    Detect gaps in macro indicators collection
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
            SELECT MAX(indicator_date) as last_update
            FROM macro_indicators
        """
        )
        result = cursor.fetchone()

        if result and result["last_update"]:
            last_update = result["last_update"]
            if isinstance(last_update, str):
                last_update = datetime.strptime(last_update, "%Y-%m-%d").date()
            elif isinstance(last_update, datetime):
                last_update = last_update.date()

            now = datetime.now().date()
            gap_days = (now - last_update).days
            gap_hours = gap_days * 24
            return gap_hours
        else:
            logger.info("No existing macro data found - first run")
            return None
    except Exception as e:
        logger.error(f"Error detecting gap: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def main():
    logger.info("Macro Indicators Collector starting...")

    # Check for backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"BACKFILL MODE: Processing last {backfill_days} days")
        collect_macro_indicators(backfill_days=int(backfill_days))
        logger.info("Backfill complete. Exiting.")
        return

    # Auto-detect and backfill gaps on startup
    gap_hours = detect_gap()
    if gap_hours:
        collection_interval_hours = 1
        if gap_hours > collection_interval_hours:
            gap_days = int(gap_hours / 24) + 1  # Add 1 day buffer
            logger.warning(
                f"⚠️  Gap detected: {gap_hours:.1f} hours ({gap_days} days) since last update"
            )
            logger.info(f"🔄 Auto-backfilling last {gap_days} days to fill gap...")

            # Limit backfill to reasonable maximum (90 days)
            if gap_days > 90:
                logger.warning(
                    f"⚠️  Gap too large ({gap_days} days), limiting to 90 days"
                )
                gap_days = 90

            collect_macro_indicators(backfill_days=gap_days)
            logger.info("✅ Gap backfill complete, resuming normal operation")
        else:
            logger.info(f"✅ No significant gap detected ({gap_hours:.1f} hours)")

    # Normal operation: schedule every 1 hour
    schedule.every(1).hours.do(collect_macro_indicators)
    collect_macro_indicators()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
