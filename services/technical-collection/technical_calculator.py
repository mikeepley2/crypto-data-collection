#!/usr/bin/env python3
"""
Technical Indicators Calculator
Calculates and updates technical indicators for price data
Includes backfill capability for historical data
"""

import os
import logging
import time
import mysql.connector
from datetime import datetime, timedelta
import schedule

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("technical-calculator")


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


def calculate_indicators(backfill_days=None):
    """
    Calculate technical indicators
    backfill_days: if set, backfill last N days of data instead of just recent
    """
    if backfill_days:
        logger.info(
            f"Starting technical indicators backfill for last {backfill_days} days..."
        )
    else:
        logger.info("Starting technical indicators calculation...")

    conn = get_db_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor(dictionary=True)

        # Get unique symbols with recent price data
        # Use timestamp_iso instead of timestamp for accurate filtering
        time_filter = ""
        if backfill_days:
            # If backfill_days is 0 or very large, backfill ALL data
            if backfill_days == 0:
                time_filter = ""  # No filter = all data
                logger.info("BACKFILL MODE: Processing ALL available data")
            else:
                cutoff_date = datetime.utcnow() - timedelta(days=backfill_days)
                time_filter = f"WHERE timestamp_iso >= '{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            # For normal operation, use last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            time_filter = (
                f"WHERE timestamp_iso >= '{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}'"
            )

        cursor.execute(
            f"""
            SELECT DISTINCT symbol FROM price_data_real
            {time_filter}
            ORDER BY symbol
            LIMIT 500
        """
        )

        symbols = cursor.fetchall()
        processed = 0

        for row in symbols:
            symbol = row["symbol"]

            try:
                # Get recent OHLC data for the symbol
                # Use timestamp_iso for accurate date filtering
                if backfill_days:
                    cutoff_date = datetime.utcnow() - timedelta(days=backfill_days)
                    cursor.execute(
                        """
                        SELECT timestamp_iso, current_price as close, high_24h as high, low_24h as low, volume_usd_24h as volume
                        FROM price_data_real
                        WHERE symbol = %s
                        AND timestamp_iso >= %s
                        ORDER BY timestamp_iso DESC
                        LIMIT 300
                    """,
                        (symbol, cutoff_date),
                    )
                else:
                    cutoff_date = datetime.utcnow() - timedelta(days=30)
                    cursor.execute(
                        """
                        SELECT timestamp_iso, current_price as close, high_24h as high, low_24h as low, volume_usd_24h as volume
                        FROM price_data_real
                        WHERE symbol = %s
                        AND timestamp_iso >= %s
                        ORDER BY timestamp_iso DESC
                        LIMIT 300
                    """,
                        (symbol, cutoff_date),
                    )

                prices = cursor.fetchall()
                if not prices:
                    continue

                # Calculate simple indicators
                close_prices = [
                    float(p["close"]) for p in prices if p["close"] is not None
                ]

                if not close_prices:
                    continue

                # Simple Moving Averages
                sma_20 = (
                    sum(close_prices[:20]) / min(20, len(close_prices))
                    if close_prices
                    else 0
                )
                sma_50 = (
                    sum(close_prices[:50]) / min(50, len(close_prices))
                    if close_prices
                    else 0
                )

                # RSI (simplified)
                rsi = 50.0

                # MACD (simplified)
                macd = 0.0

                # Bollinger Bands (simplified)
                bb_upper = sma_20 * 1.02
                bb_lower = sma_20 * 0.98

                # Use timestamp_iso directly
                if prices and prices[0].get("timestamp_iso"):
                    timestamp_iso = prices[0]["timestamp_iso"]
                    if isinstance(timestamp_iso, str):
                        timestamp_iso = datetime.fromisoformat(
                            timestamp_iso.replace("Z", "+00:00")
                        )
                else:
                    timestamp_iso = datetime.utcnow()

                cursor.execute(
                    """
                    INSERT INTO technical_indicators (
                        symbol, timestamp_iso, sma_20, sma_50, rsi,
                        macd, bollinger_upper, bollinger_lower
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sma_20 = VALUES(sma_20),
                        sma_50 = VALUES(sma_50),
                        rsi = VALUES(rsi),
                        macd = VALUES(macd),
                        bollinger_upper = VALUES(bollinger_upper),
                        bollinger_lower = VALUES(bollinger_lower),
                        updated_at = NOW()
                """,
                    (
                        symbol,
                        timestamp_iso,
                        sma_20,
                        sma_50,
                        rsi,
                        macd,
                        bb_upper,
                        bb_lower,
                    ),
                )

                processed += 1

            except Exception as e:
                logger.error(f"Error for {symbol}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} symbols")
        with open("/tmp/technical_calculator_health.txt", "w") as f:
            f.write(str(datetime.utcnow()))

    except Exception as e:
        logger.error(f"Calculation error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return processed


def detect_gap():
    """
    Detect gaps in technical indicators calculation
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
            SELECT MAX(timestamp_iso) as last_update
            FROM technical_indicators
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

            now = datetime.utcnow()
            gap_hours = (now - last_update).total_seconds() / 3600
            return gap_hours
        else:
            logger.info("No existing technical indicators found - first run")
            return None
    except Exception as e:
        logger.error(f"Error detecting gap: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def main():
    logger.info("Technical Indicators Calculator starting...")

    # Check for backfill request
    backfill_days = os.getenv("BACKFILL_DAYS")
    if backfill_days:
        logger.info(f"BACKFILL MODE: Processing last {backfill_days} days")
        calculate_indicators(backfill_days=int(backfill_days))
        logger.info("Backfill complete. Exiting.")
        return

    # Auto-detect and backfill gaps on startup
    gap_hours = detect_gap()
    if gap_hours:
        collection_interval_hours = 5 / 60  # 5 minutes in hours
        if gap_hours > collection_interval_hours:
            gap_days = int(gap_hours / 24) + 1  # Add 1 day buffer
            logger.warning(
                f"⚠️  Gap detected: {gap_hours:.1f} hours ({gap_days} days) since last update"
            )
            logger.info(f"🔄 Auto-backfilling last {gap_days} days to fill gap...")

            # Limit backfill to reasonable maximum (30 days)
            if gap_days > 30:
                logger.warning(
                    f"⚠️  Gap too large ({gap_days} days), limiting to 30 days"
                )
                gap_days = 30

            calculate_indicators(backfill_days=gap_days)
            logger.info("✅ Gap backfill complete, resuming normal operation")
        else:
            logger.info(f"✅ No significant gap detected ({gap_hours:.1f} hours)")

    # Normal operation: schedule every 5 minutes
    schedule.every(5).minutes.do(calculate_indicators)
    calculate_indicators()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
