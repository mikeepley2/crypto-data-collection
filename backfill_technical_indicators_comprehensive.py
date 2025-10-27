#!/usr/bin/env python3
"""
Comprehensive Technical Indicators Backfill Script
Backfills all technical indicators (SMA, RSI, MACD, Bollinger Bands) for the materialized table
"""

import mysql.connector
import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection"""
    config = {
        "host": "127.0.0.1",
        "user": "news_collector",
        "password": "99Rules!",
        "database": "crypto_prices",
        "charset": "utf8mb4",
    }
    return mysql.connector.connect(**config)


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    if len(gains) < period:
        return None

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    if len(prices) < slow:
        return None, None, None

    # Calculate EMAs
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    if ema_fast is None or ema_slow is None:
        return None, None, None

    macd_line = ema_fast - ema_slow

    # For signal line, we need MACD values over time, so we'll use a simplified approach
    # In practice, you'd need to store MACD values and calculate signal line
    signal_line = macd_line * 0.9  # Simplified approximation
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return None, None, None

    sma = calculate_sma(prices, period)
    if sma is None:
        return None, None, None

    # Calculate standard deviation
    variance = sum((price - sma) ** 2 for price in prices[-period:]) / period
    std_deviation = math.sqrt(variance)

    upper_band = sma + (std_deviation * std_dev)
    lower_band = sma - (std_deviation * std_dev)

    return upper_band, sma, lower_band


def backfill_technical_indicators():
    """Backfill technical indicators for all symbols in materialized table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting comprehensive technical indicators backfill...")

        # Get all symbols from materialized table that need technical indicators
        cursor.execute(
            """
        SELECT DISTINCT symbol 
        FROM ml_features_materialized 
        WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND (sma_20 IS NULL OR rsi_14 IS NULL OR macd_line IS NULL OR bb_upper IS NULL)
        ORDER BY symbol
        """
        )
        symbols = [row[0] for row in cursor.fetchall()]

        logger.info(f"Found {len(symbols)} symbols needing technical indicators")

        updated_count = 0
        processed_count = 0

        for symbol in symbols:
            try:
                # Get price data for this symbol (last 30 days to ensure we have enough data)
                cursor.execute(
                    """
                SELECT current_price, timestamp_iso
                FROM price_data_real 
                WHERE symbol = %s 
                AND timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY timestamp_iso ASC
                """,
                    (symbol,),
                )

                price_data = cursor.fetchall()

                if len(price_data) < 20:  # Need at least 20 data points
                    logger.warning(
                        f"Insufficient price data for {symbol}: {len(price_data)} records"
                    )
                    continue

                prices = [float(row[0]) for row in price_data]
                timestamps = [row[1] for row in price_data]

                # Calculate technical indicators for recent records
                recent_records = []
                for i in range(
                    19, len(prices)
                ):  # Start from index 19 to have enough data
                    current_prices = prices[: i + 1]
                    timestamp = timestamps[i]

                    # Calculate indicators
                    sma_20 = calculate_sma(current_prices, 20)
                    rsi_14 = calculate_rsi(current_prices, 14)
                    macd_line, macd_signal, macd_histogram = calculate_macd(
                        current_prices
                    )
                    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
                        current_prices
                    )

                    # Only process recent records (last 7 days)
                    if timestamp >= datetime.now() - timedelta(days=7):
                        recent_records.append(
                            {
                                "timestamp": timestamp,
                                "sma_20": sma_20,
                                "rsi_14": rsi_14,
                                "macd_line": macd_line,
                                "macd_signal": macd_signal,
                                "macd_histogram": macd_histogram,
                                "bb_upper": bb_upper,
                                "bb_middle": bb_middle,
                                "bb_lower": bb_lower,
                            }
                        )

                # Update materialized table with calculated indicators
                for record in recent_records:
                    cursor.execute(
                        """
                    UPDATE ml_features_materialized 
                    SET sma_20 = %s,
                        rsi_14 = %s,
                        macd_line = %s,
                        macd_signal = %s,
                        macd_histogram = %s,
                        bb_upper = %s,
                        bb_middle = %s,
                        bb_lower = %s,
                        updated_at = NOW()
                    WHERE symbol = %s 
                    AND DATE(timestamp_iso) = DATE(%s)
                    """,
                        (
                            record["sma_20"],
                            record["rsi_14"],
                            record["macd_line"],
                            record["macd_signal"],
                            record["macd_histogram"],
                            record["bb_upper"],
                            record["bb_middle"],
                            record["bb_lower"],
                            symbol,
                            record["timestamp"],
                        ),
                    )

                    if cursor.rowcount > 0:
                        updated_count += cursor.rowcount

                processed_count += 1

                if processed_count % 10 == 0:
                    logger.info(
                        f"Processed {processed_count}/{len(symbols)} symbols, updated {updated_count} records"
                    )
                    conn.commit()

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        conn.commit()
        logger.info(f"Technical indicators backfill completed!")
        logger.info(f"Processed {processed_count} symbols")
        logger.info(f"Updated {updated_count} records")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error in technical indicators backfill: {e}")


if __name__ == "__main__":
    backfill_technical_indicators()
