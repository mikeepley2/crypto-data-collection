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

# Import centralized scheduling configuration
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None
    create_schedule_for_collector = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("macro-collector")

# FRED API endpoint and configuration
FRED_API_BASE = "https://api.stlouisfed.org/fred"
# FRED API key - check env var first, then use valid default from aitest folder
FRED_API_KEY = os.getenv("FRED_API_KEY", "35478996c5e061d0fc99fc73f5ce348d")

# Placeholder creation configuration
ENSURE_PLACEHOLDERS = os.getenv("ENSURE_PLACEHOLDERS", "true").lower() == "true"
PLACEHOLDER_LOOKBACK_DAYS = int(os.getenv("PLACEHOLDER_LOOKBACK_DAYS", "7"))
MAX_BACKFILL_DAYS = int(os.getenv("MAX_BACKFILL_DAYS", "30"))

# Mapping of indicator names to FRED series IDs - Complete ML feature coverage
FRED_SERIES = {
    # Daily indicators (high frequency)
    "DGS10": "DGS10",        # 10-Year Treasury Daily
    "DGS2": "DGS2",          # 2-Year Treasury Daily
    "DGS30": "DGS30",        # 30-Year Treasury Daily
    "DGS1": "DGS1",          # 1-Year Treasury Daily  
    "DEXJPUS": "DEXJPUS",    # USD/JPY Exchange Rate Daily
    "DEXUSEU": "DEXUSEU",    # USD/EUR Exchange Rate Daily
    "VIX": "VIXCLS",         # VIX Volatility Index Daily
    
    # Monthly indicators
    "UNRATE": "UNRATE",      # Unemployment Rate Monthly
    "CPIAUCSL": "CPIAUCSL",  # Consumer Price Index Monthly  
    "FEDFUNDS": "FEDFUNDS",  # Federal Funds Rate Monthly
    "UMCSENT": "UMCSENT",    # Consumer Confidence Monthly
    "RSAFS": "RSAFS",        # Retail Sales Monthly
    "INDPRO": "INDPRO",      # Industrial Production Monthly
    "PAYEMS": "PAYEMS",      # Employment Level Monthly
    "HOUST": "HOUST",        # Housing Starts Monthly
    "CSUSHPISA": "CSUSHPISA", # Case-Shiller Home Price Index
    
    # Quarterly indicators  
    "GDP": "GDPC1",          # Real GDP Quarterly
    "GDPPOT": "GDPPOT",      # Potential GDP Quarterly
    
    # Weekly indicators
    "DFF": "DFF",            # Federal Funds Daily Rate
    "TB3MS": "TB3MS",        # 3-Month Treasury Monthly
    "TB6MS": "TB6MS",        # 6-Month Treasury Monthly
    
    # Additional ML-relevant indicators
    "MORTGAGE30US": "MORTGAGE30US", # 30Y Fixed Rate Mortgage
    "BAMLH0A0HYM2": "BAMLH0A0HYM2", # High Yield Credit Spread
    "T5YIE": "T5YIE",        # 5Y5Y Inflation Expectation  
    "DTWEXBGS": "DTWEXBGS",  # Trade Weighted US Dollar Index
    
    # Legacy mappings (for backward compatibility)
    "US_UNEMPLOYMENT": "UNRATE",
    "US_INFLATION": "CPIAUCSL", 
    "FEDERAL_FUNDS_RATE": "FEDFUNDS",
    "US_GDP": "GDPC1",
    "INTEREST_RATE": "FEDFUNDS",
    "EMPLOYMENT_RATE": "PAYEMS",
    "CONSUMER_CONFIDENCE": "UMCSENT",
    "RETAIL_SALES": "RSAFS",
    "INDUSTRIAL_PRODUCTION": "INDPRO",
    "GDP_GROWTH": "GDPC1",
    "CPI_INFLATION": "CPIAUCSL"
}
    "CPIAUCSL": "CPIAUCSL",  # Consumer Price Index Monthly
    "FEDFUNDS": "FEDFUNDS",  # Federal Funds Rate Monthly
    
    # Quarterly indicators
    "GDP": "GDPC1",          # Real GDP Quarterly
    
    # Legacy mappings (for backward compatibility)
    "US_UNEMPLOYMENT": "UNRATE",
    "US_INFLATION": "CPIAUCSL",
    "FEDERAL_FUNDS_RATE": "FEDFUNDS",
    "US_GDP": "GDPC1"
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


def fetch_fred_data(series_id, backfill_days=None, start_date=None):
    """
    Fetch data from FRED API with enhanced date handling
    Returns latest value if backfill_days is None, or all observations for backfill
    
    Args:
        series_id: FRED series identifier
        backfill_days: Number of days to look back (overrides start_date)
        start_date: Specific start date for fetching (YYYY-MM-DD format)
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
            calculated_start = (datetime.now() - timedelta(days=backfill_days)).strftime(
                "%Y-%m-%d"
            )
            params["observation_start"] = calculated_start
        elif start_date:
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


def ensure_placeholder_records(cursor, target_date=None, lookback_days=PLACEHOLDER_LOOKBACK_DAYS):
    """
    Ensure placeholder records exist for all macro indicators for the specified date range
    
    Args:
        cursor: Database cursor
        target_date: Specific date to create placeholders for (if None, uses lookback)
        lookback_days: How many days back to create placeholders
        
    Returns:
        Number of placeholder records created
    """
    if not ENSURE_PLACEHOLDERS:
        logger.debug("Placeholder creation disabled")
        return 0
    
    logger.info("🔧 Ensuring macro indicator placeholder records exist...")
    
    placeholders_created = 0
    
    try:
        # Determine date range
        if target_date:
            start_date = end_date = target_date
        else:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback_days)
        
        logger.info(f"   Creating placeholders from {start_date} to {end_date}")
        
        # Create placeholders for each indicator and date
        current_date = start_date
        while current_date <= end_date:
            for indicator_name in FRED_SERIES.keys():
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, 
                         data_completeness_percentage, collected_at)
                        VALUES (%s, %s, NULL, 'placeholder_auto', 0.0, NOW())
                    """, (indicator_name, current_date))
                    
                    if cursor.rowcount > 0:
                        placeholders_created += 1
                        logger.debug(f"Created placeholder: {indicator_name} on {current_date}")
                        
                except Exception as e:
                    logger.error(f"Error creating placeholder for {indicator_name} on {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        logger.info(f"✅ Created {placeholders_created} placeholder records")
        return placeholders_created
        
    except Exception as e:
        logger.error(f"Error ensuring placeholder records: {e}")
        return 0


def calculate_macro_completeness(record_data):
    """
    Calculate completeness percentage for a macro indicator record
    
    Args:
        record_data: Dict containing record field values
        
    Returns:
        Completeness percentage (0.0 to 100.0)
    """
    required_fields = ['indicator_name', 'indicator_date', 'value', 'data_source']
    
    populated_fields = sum(1 for field in required_fields 
                          if record_data.get(field) is not None 
                          and str(record_data.get(field)).strip() != '')
    
    return (populated_fields / len(required_fields)) * 100.0


def update_record_completeness(cursor, indicator_name, indicator_date, record_data):
    """
    Update the completeness percentage for a specific macro record
    
    Args:
        cursor: Database cursor
        indicator_name: Name of the indicator
        indicator_date: Date of the record
        record_data: Dict with the record's field values
        
    Returns:
        True if update was successful
    """
    try:
        completeness = calculate_macro_completeness(record_data)
        
        cursor.execute("""
            UPDATE macro_indicators
            SET data_completeness_percentage = %s
            WHERE indicator_name = %s AND indicator_date = %s
        """, (completeness, indicator_name, indicator_date))
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Error updating completeness for {indicator_name} on {indicator_date}: {e}")
        return False


def collect_macro_indicators_smart():
    """
    Smart collection that uses different lookback periods for different indicator types
    Based on centralized scheduling configuration
    """
    logger.info("Starting smart macro indicators collection...")
    
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        total_processed = 0
        
        # Step 1: Ensure placeholder records exist
        placeholders_created = 0
        if ENSURE_PLACEHOLDERS:
            placeholders_created = ensure_placeholder_records(cursor)
            conn.commit()
        
        # Step 2: Collect real data for different indicator types
        
        # Daily indicators - look back 7 days
        daily_indicators = ["DGS10", "DGS2", "DEXJPUS", "DEXUSEU", "VIX"]
        for indicator in daily_indicators:
            if indicator in FRED_SERIES:
                data = fetch_fred_data(FRED_SERIES[indicator], backfill_days=7)
                processed = insert_indicator_data(cursor, indicator, data, "daily_collection")
                total_processed += processed
                logger.info(f"Daily {indicator}: {processed} records")
        
        # Monthly indicators - look back 35 days  
        monthly_indicators = ["UNRATE", "CPIAUCSL", "FEDFUNDS"]
        for indicator in monthly_indicators:
            if indicator in FRED_SERIES:
                data = fetch_fred_data(FRED_SERIES[indicator], backfill_days=35)
                processed = insert_indicator_data(cursor, indicator, data, "monthly_collection")
                total_processed += processed
                logger.info(f"Monthly {indicator}: {processed} records")
        
        # Quarterly indicators - look back 95 days
        quarterly_indicators = ["GDP"]
        for indicator in quarterly_indicators:
            if indicator in FRED_SERIES:
                data = fetch_fred_data(FRED_SERIES[indicator], backfill_days=95)
                processed = insert_indicator_data(cursor, indicator, data, "quarterly_collection")
                total_processed += processed
                logger.info(f"Quarterly {indicator}: {processed} records")
        
        conn.commit()
        logger.info(f"Smart collection complete: {total_processed} total records")
        logger.info(f"Placeholders created: {placeholders_created}")
        
        # Update health check
        with open("/tmp/macro_collector_health.txt", "w") as f:
            f.write(f"{datetime.utcnow()}: {total_processed} records")
        
        return total_processed
        
    except Exception as e:
        logger.error(f"Smart collection error: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


def insert_indicator_data(cursor, indicator_name, observations, data_source):
    """
    Insert indicator data into database with duplicate handling and completeness tracking
    """
    if not observations:
        return 0
    
    inserted = 0
    
    if isinstance(observations, list):
        # Multiple observations (backfill mode)
        for obs in observations:
            try:
                cursor.execute(
                    """
                    INSERT INTO macro_indicators 
                    (indicator_name, indicator_date, value, data_source, collected_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        value = VALUES(value),
                        data_source = VALUES(data_source),
                        collected_at = NOW()
                """,
                    (indicator_name, obs["date"], obs["value"], data_source)
                )
                
                if cursor.rowcount > 0:
                    inserted += 1
                    
                    # Update completeness percentage
                    record_data = {
                        'indicator_name': indicator_name,
                        'indicator_date': obs["date"],
                        'value': obs["value"],
                        'data_source': data_source
                    }
                    update_record_completeness(cursor, indicator_name, obs["date"], record_data)
                    
            except Exception as e:
                logger.debug(f"Error inserting {indicator_name} for {obs['date']}: {e}")
    else:
        # Single observation (current mode)
        try:
            cursor.execute(
                """
                INSERT INTO macro_indicators 
                (indicator_name, indicator_date, value, data_source, collected_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    value = VALUES(value),
                    data_source = VALUES(data_source),
                    collected_at = NOW()
            """,
                (indicator_name, datetime.now().date(), observations, data_source)
            )
            
            if cursor.rowcount > 0:
                inserted = 1
                
                # Update completeness percentage
                record_data = {
                    'indicator_name': indicator_name,
                    'indicator_date': datetime.now().date(),
                    'value': observations,
                    'data_source': data_source
                }
                update_record_completeness(cursor, indicator_name, datetime.now().date(), record_data)
                
        except Exception as e:
            logger.error(f"Error inserting {indicator_name}: {e}")
    
    return inserted


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

                # Use the enhanced insertion logic
                inserted_count = insert_indicator_data(
                    cursor, indicator_name, data, 
                    "FRED_backfill" if backfill_days else "FRED_API"
                )
                processed += inserted_count
                
                if backfill_days:
                    logger.info(f"Backfilled {inserted_count} observations for {indicator_name}")
                else:
                    logger.info(f"Collected {indicator_name}: {data if data is not None else 'N/A'} ({inserted_count} records)")

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
        # Use centralized scheduling config with fallback
        if get_collector_schedule:
            config = get_collector_schedule('macro')
            collection_interval_hours = config['frequency_hours']
        else:
            collection_interval_hours = 1  # Fallback: 1 hour
        
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

    # Use smart collection by default, with centralized scheduling
    collection_function = collect_macro_indicators_smart
    
    # Use centralized scheduling config with fallback
    if create_schedule_for_collector:
        try:
            create_schedule_for_collector('macro', schedule, collection_function)
            logger.info("✅ Using centralized scheduling configuration for smart collection")
        except Exception as e:
            logger.warning(f"Centralized config failed, using fallback: {e}")
            schedule.every(1).hours.do(collection_function)
    else:
        logger.info("Using fallback: hourly collection")
        schedule.every(1).hours.do(collection_function)
    
    # Run initial collection
    collection_function()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
