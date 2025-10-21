"""
Bollinger Bands Backfill Script
Calculates and populates Bollinger Upper/Lower bands for all technical indicators
Formula: BB = SMA 20 +/- (2 * StdDev of prices over 20 periods)
"""

import mysql.connector
from datetime import datetime, timedelta
import math

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}


def calculate_bollinger_bands():
    """Calculate and backfill Bollinger Bands for all records"""

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Create a separate cursor for nested queries to avoid cursor reuse issues
        price_cursor = mysql.connector.connect(**config).cursor()

        print("=" * 80)
        print("BOLLINGER BANDS BACKFILL")
        print("=" * 80)
        print()

        # 1. Get all distinct symbols
        cursor.execute(
            "SELECT DISTINCT symbol FROM technical_indicators ORDER BY symbol"
        )
        symbols = [row[0] for row in cursor.fetchall()]

        print(f"Processing {len(symbols)} cryptocurrency symbols...")
        print()

        total_processed = 0
        total_updated = 0

        for idx, symbol in enumerate(symbols, 1):
            if idx % 50 == 0:
                print(f"Progress: {idx}/{len(symbols)} symbols processed, Updated: {total_updated:,}...")

            try:
                # Get all technical records for this symbol, ordered by time
                cursor.execute(
                    """
                SELECT 
                    id,
                    symbol,
                    timestamp_iso,
                    sma_20
                FROM technical_indicators
                WHERE symbol = %s
                ORDER BY timestamp_iso ASC
                """,
                    (symbol,),
                )

                records = cursor.fetchall()

                # For each record, get the last 20 prices to calculate std dev
                for record_id, sym, timestamp_iso, sma_20 in records:
                    if sma_20 is None:
                        continue

                    # Convert datetime to Unix milliseconds for comparison with price_data_real
                    from datetime import datetime as dt
                    timestamp_ms = int(dt.timestamp(timestamp_iso) * 1000)
                    
                    # Get last 20 prices before this timestamp using separate cursor
                    price_cursor.execute(
                        """
                    SELECT current_price
                    FROM price_data_real
                    WHERE symbol = %s
                    AND timestamp < %s
                    ORDER BY timestamp DESC
                    LIMIT 20
                    """,
                        (symbol, timestamp_ms),
                    )

                    prices = [row[0] for row in price_cursor.fetchall()]

                    if len(prices) >= 2:  # Need at least 2 prices for std dev
                        prices = sorted(
                            prices, reverse=False
                        )  # Get in chronological order

                        # Calculate standard deviation
                        mean = sum(prices) / len(prices)
                        variance = sum((x - mean) ** 2 for x in prices) / len(prices)
                        std_dev = math.sqrt(variance)

                        # Calculate Bollinger Bands
                        bb_upper = sma_20 + (2 * std_dev)
                        bb_lower = sma_20 - (2 * std_dev)

                        # Update the record using main cursor
                        cursor.execute(
                            """
                        UPDATE technical_indicators
                        SET 
                            bollinger_upper = %s,
                            bollinger_lower = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                            (bb_upper, bb_lower, record_id),
                        )

                        total_updated += 1

                    total_processed += 1

                    # Commit every 1000 records
                    if total_processed % 1000 == 0:
                        conn.commit()
                        print(f"  Processed {total_processed:,} records, Updated: {total_updated:,}")

            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                conn.rollback()
                continue

        conn.commit()

        print()
        print("=" * 80)
        print("BACKFILL COMPLETE")
        print("=" * 80)
        print(f"Total records processed: {total_processed:,}")
        print(f"Total records updated: {total_updated:,}")
        print(
            f"Success rate: {(total_updated/total_processed*100):.1f}%"
            if total_processed > 0
            else 0
        )
        print()

        # Verify results
        cursor.execute(
            """
        SELECT 
            SUM(CASE WHEN bollinger_upper IS NOT NULL THEN 1 ELSE 0 END) as with_bb,
            COUNT(*) as total
        FROM technical_indicators
        """
        )

        verification = cursor.fetchone()
        bb_pct = (verification[0] / verification[1] * 100) if verification[1] > 0 else 0
        print(
            f"Bollinger Bands now populated: {verification[0]:,} / {verification[1]:,} ({bb_pct:.1f}%)"
        )

        cursor.close()
        price_cursor.close()
        conn.close()

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Bollinger Bands backfill...")
    calculate_bollinger_bands()
    print("\nDone!")
