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
import argparse
import sys
import numpy as np

# Import centralized scheduling configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
    from shared.database_config import get_db_connection as shared_get_db_connection
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None
    create_schedule_for_collector = None
    shared_get_db_connection = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("technical-calculator")


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices)
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # Start with SMA
    
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return 50.0  # Neutral RSI for insufficient data
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    
    if len(gains) < period:
        return 50.0
    
    # Use Wilder's smoothing (similar to EMA with alpha = 1/period)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Apply smoothing for remaining periods
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    if len(prices) < slow:
        return 0.0, 0.0, 0.0  # MACD, Signal, Histogram
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    macd_line = ema_fast - ema_slow
    
    # For signal line, we need MACD values over time, but we'll simplify for single point
    signal_line = macd_line * 0.9  # Simplified signal approximation
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands using standard deviation"""
    if len(prices) < period:
        sma = sum(prices) / len(prices)
        return sma * 1.02, sma, sma * 0.98  # Fallback to simple bands
    
    recent_prices = prices[-period:]
    sma = sum(recent_prices) / period
    
    # Calculate standard deviation
    variance = sum((price - sma) ** 2 for price in recent_prices) / period
    std = variance ** 0.5
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return upper_band, sma, lower_band


def calculate_stochastic(highs, lows, closes, k_period=14, d_period=3):
    """Calculate Stochastic Oscillator"""
    if len(closes) < k_period:
        return 50.0, 50.0  # %K, %D
    
    recent_highs = highs[-k_period:]
    recent_lows = lows[-k_period:]
    current_close = closes[-1]
    
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    
    if highest_high == lowest_low:
        k_percent = 50.0
    else:
        k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
    
    # Simplified %D (normally would be SMA of %K values)
    d_percent = k_percent * 0.9
    
    return k_percent, d_percent


def calculate_atr(highs, lows, closes, period=14):
    """Calculate Average True Range"""
    if len(closes) < 2:
        return 0.0
    
    true_ranges = []
    for i in range(1, min(len(closes), period + 1)):
        high_low = highs[i] - lows[i]
        high_close_prev = abs(highs[i] - closes[i-1])
        low_close_prev = abs(lows[i] - closes[i-1])
        
        true_range = max(high_low, high_close_prev, low_close_prev)
        true_ranges.append(true_range)
    
    return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0


def get_db_connection():
    """Get database connection with fallback to shared config"""
    if shared_get_db_connection:
        try:
            return shared_get_db_connection()
        except Exception as e:
            logger.warning(f"Shared DB config failed, using fallback: {e}")
    
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "172.22.32.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def calculate_indicators(backfill_days=None, force_recalc=False):
    """
    Calculate technical indicators
    backfill_days: if set, backfill last N days of data instead of just recent
    force_recalc: if True, recalculate even if data exists
    """
    if backfill_days:
        logger.info(
            f"Starting technical indicators backfill for last {backfill_days} days..."
        )
    else:
        logger.info("Starting technical indicators calculation...")
    
    if force_recalc:
        logger.info("Force recalculation mode - will overwrite existing indicators")

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
                cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=backfill_days)
                time_filter = f"WHERE timestamp_iso >= '{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            # For normal operation, use last 30 days
            cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=30)
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
                # Get all OHLC data for the symbol in the time range
                if backfill_days:
                    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=backfill_days)
                    cursor.execute(
                        """
                        SELECT timestamp_iso, current_price as close, high_24h as high, low_24h as low, volume_usd_24h as volume
                        FROM price_data_real
                        WHERE symbol = %s
                        AND timestamp_iso >= %s
                        ORDER BY timestamp_iso ASC
                        LIMIT 10000
                    """,
                        (symbol, cutoff_date),
                    )
                else:
                    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=30)
                    cursor.execute(
                        """
                        SELECT timestamp_iso, current_price as close, high_24h as high, low_24h as low, volume_usd_24h as volume
                        FROM price_data_real
                        WHERE symbol = %s
                        AND timestamp_iso >= %s
                        ORDER BY timestamp_iso ASC
                        LIMIT 300
                    """,
                        (symbol, cutoff_date),
                    )

                prices = cursor.fetchall()
                if not prices:
                    continue

                # Filter valid prices
                valid_prices = [p for p in prices if p["close"] is not None]
                if len(valid_prices) < 20:  # Need at least 20 for indicators
                    continue

                # For backfill mode, calculate indicators for each timestamp
                # For normal mode, calculate for latest only
                if backfill_days:
                    # Process each price point that needs indicators
                    price_values = [float(p["close"]) for p in valid_prices]

                    for i in range(
                        19, len(valid_prices)
                    ):  # Start from index 19 to have 20 prices
                        current_prices = price_values[: i + 1]
                        price_record = valid_prices[i]

                        # Calculate indicators based on historical prices up to this point
                        sma_20 = (
                            sum(current_prices[-20:]) / min(20, len(current_prices))
                            if len(current_prices) >= 20
                            else sum(current_prices) / len(current_prices)
                        )
                        sma_50 = (
                            sum(current_prices[-50:]) / min(50, len(current_prices))
                            if len(current_prices) >= 50
                            else sum(current_prices) / len(current_prices)
                        )

                        # RSI calculation
                        rsi = calculate_rsi(current_prices, 14)

                        # MACD calculation
                        macd_line, macd_signal, macd_histogram = calculate_macd(current_prices)
                        macd = macd_line

                        # Bollinger Bands calculation
                        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(current_prices, 20, 2)

                        # Get timestamp_iso
                        timestamp_iso = price_record["timestamp_iso"]
                        if isinstance(timestamp_iso, str):
                            timestamp_iso = datetime.fromisoformat(
                                timestamp_iso.replace("Z", "+00:00")
                            )

                        # Always insert/update - ON DUPLICATE KEY UPDATE handles existing records
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
                        if cursor.rowcount > 0:  # Count if inserted or updated
                            processed += 1
                else:
                    # Normal mode: calculate for latest only
                    close_prices = [
                        float(p["close"])
                        for p in valid_prices
                        if p["close"] is not None
                    ]

                    # Simple Moving Averages
                    sma_20 = (
                        sum(close_prices[-20:]) / min(20, len(close_prices))
                        if close_prices
                        else 0
                    )
                    sma_50 = (
                        sum(close_prices[-50:]) / min(50, len(close_prices))
                        if close_prices
                        else 0
                    )

                    # RSI calculation
                    rsi = calculate_rsi(close_prices, 14)

                    # MACD calculation
                    macd_line, macd_signal, macd_histogram = calculate_macd(close_prices)
                    macd = macd_line

                    # Bollinger Bands calculation
                    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close_prices, 20, 2)

                    # Use latest timestamp
                    if valid_prices and valid_prices[-1].get("timestamp_iso"):
                        timestamp_iso = valid_prices[-1]["timestamp_iso"]
                        if isinstance(timestamp_iso, str):
                            timestamp_iso = datetime.fromisoformat(
                                timestamp_iso.replace("Z", "+00:00")
                            )
                    else:
                        timestamp_iso = datetime.now().replace(tzinfo=None)

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
            f.write(str(datetime.now().replace(tzinfo=None)))

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

            now = datetime.now().replace(tzinfo=None)
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
        # Use centralized scheduling config with fallback
        if get_collector_schedule:
            config = get_collector_schedule('technical')
            collection_interval_hours = config['frequency_hours']
        else:
            collection_interval_hours = 5 / 60  # Fallback: 5 minutes in hours
        
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
    # Use centralized scheduling config with fallback
    if create_schedule_for_collector:
        try:
            create_schedule_for_collector('technical', schedule, calculate_indicators)
            logger.info("✅ Using centralized scheduling configuration")
        except Exception as e:
            logger.warning(f"Centralized config failed, using fallback: {e}")
            schedule.every(5).minutes.do(calculate_indicators)
    else:
        schedule.every(5).minutes.do(calculate_indicators)
    
    calculate_indicators()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Technical Indicators Calculator')
    parser.add_argument('--test', action='store_true', help='Test connection and exit')
    parser.add_argument('--backfill', type=int, help='Backfill last N days')
    parser.add_argument('--force-recalc', action='store_true', help='Force recalculation of existing data')
    
    args = parser.parse_args()
    
    if args.test:
        # Test database connection
        conn = get_db_connection()
        if conn:
            logger.info("✅ Database connection test passed")
            conn.close()
            sys.exit(0)
        else:
            logger.error("❌ Database connection test failed")
            sys.exit(1)
    
    if args.backfill:
        logger.info(f"Running backfill for {args.backfill} days")
        calculate_indicators(backfill_days=args.backfill, force_recalc=args.force_recalc)
        sys.exit(0)
    
    # Default: run main service
    main()
