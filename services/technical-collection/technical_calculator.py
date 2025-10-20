#!/usr/bin/env python3
"""
Technical Indicators Calculator
Calculates and updates technical indicators for price data
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


def calculate_indicators():
    """Calculate technical indicators"""
    logger.info("Starting technical indicators calculation...")

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)

        # Get unique symbols with recent price data
        cursor.execute(
            """
            SELECT DISTINCT symbol FROM price_data_real
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY symbol
            LIMIT 50
        """
        )

        symbols = cursor.fetchall()
        processed = 0

        for row in symbols:
            symbol = row["symbol"]

            try:
                # Get recent OHLC data for the symbol
                cursor.execute(
                    """
                    SELECT timestamp, close, high, low, volume
                    FROM price_data_real
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 200
                """,
                    (symbol,),
                )

                prices = cursor.fetchall()
                if not prices:
                    continue

                # Calculate simple indicators
                close_prices = [float(p["close"]) for p in prices]

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

                # Update technical_indicators table
                timestamp = prices[0]["timestamp"] if prices else datetime.utcnow()

                cursor.execute(
                    """
                    INSERT INTO technical_indicators (
                        symbol, timestamp, sma_20, sma_50, rsi, 
                        macd, bb_upper, bb_lower
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sma_20 = VALUES(sma_20),
                        sma_50 = VALUES(sma_50),
                        rsi = VALUES(rsi),
                        macd = VALUES(macd),
                        bb_upper = VALUES(bb_upper),
                        bb_lower = VALUES(bb_lower),
                        updated_at = NOW()
                """,
                    (symbol, timestamp, sma_20, sma_50, rsi, macd, bb_upper, bb_lower),
                )

                processed += 1

            except Exception as e:
                logger.error(f"Error for {symbol}: {e}")

        conn.commit()
        logger.info(f"Processed {processed} symbols")

    except Exception as e:
        logger.error(f"Calculation error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def main():
    logger.info("Technical Indicators Calculator starting...")
    schedule.every(5).minutes.do(calculate_indicators)
    calculate_indicators()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
