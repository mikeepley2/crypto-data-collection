#!/usr/bin/env python3
"""
Macro Indicators Backfill Script
Backfills macro indicators data into the materialized table
"""

import mysql.connector
import logging
from datetime import datetime, timedelta

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


def backfill_macro_indicators():
    """Backfill macro indicators data into materialized table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting macro indicators backfill...")

        # Get latest macro indicators for each type
        cursor.execute(
            """
        SELECT 
            indicator_name,
            value,
            indicator_date
        FROM macro_indicators
        WHERE indicator_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND value IS NOT NULL
        ORDER BY indicator_name, indicator_date DESC
        """
        )
        macro_data = cursor.fetchall()

        logger.info(f"Found {len(macro_data)} macro indicator records")

        if len(macro_data) == 0:
            logger.warning("No macro indicators found!")
            return

        # Group macro data by indicator name and get latest values
        macro_dict = {}
        for indicator_name, value, indicator_date in macro_data:
            if indicator_name not in macro_dict:
                macro_dict[indicator_name] = (value, indicator_date)

        logger.info(f"Processing {len(macro_dict)} unique macro indicators")

        # Get all symbols from materialized table that need macro indicators
        cursor.execute(
            """
        SELECT DISTINCT symbol, timestamp_iso
        FROM ml_features_materialized
        WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        AND (vix IS NULL OR spx IS NULL OR dxy IS NULL OR tnx IS NULL OR fed_funds_rate IS NULL)
        ORDER BY symbol, timestamp_iso
        """
        )
        materialized_records = cursor.fetchall()

        logger.info(
            f"Found {len(materialized_records)} materialized records needing macro indicators"
        )

        updated_count = 0

        for symbol, timestamp_iso in materialized_records:
            try:
                # Map macro indicators to materialized table columns
                vix_value = macro_dict.get("VIX", (None, None))[0]
                spx_value = macro_dict.get("SPX", (None, None))[0]
                dxy_value = macro_dict.get("DXY", (None, None))[0]
                tnx_value = macro_dict.get("US_10Y_YIELD", (None, None))[0]
                fed_value = macro_dict.get("US_FED_FUNDS_RATE", (None, None))[0]
                gold_value = macro_dict.get("GOLD_PRICE", (None, None))[0]
                oil_value = macro_dict.get("OIL_PRICE", (None, None))[0]

                # Update materialized table with macro indicators
                cursor.execute(
                    """
                UPDATE ml_features_materialized 
                SET vix = %s,
                    spx = %s,
                    dxy = %s,
                    tnx = %s,
                    fed_funds_rate = %s,
                    gold_price = %s,
                    oil_price = %s,
                    updated_at = NOW()
                WHERE symbol = %s 
                AND timestamp_iso = %s
                """,
                    (
                        vix_value,
                        spx_value,
                        dxy_value,
                        tnx_value,
                        fed_value,
                        gold_value,
                        oil_value,
                        symbol,
                        timestamp_iso,
                    ),
                )

                if cursor.rowcount > 0:
                    updated_count += cursor.rowcount

            except Exception as e:
                logger.error(f"Error processing {symbol} at {timestamp_iso}: {e}")
                continue

        conn.commit()
        logger.info(f"Macro indicators backfill completed!")
        logger.info(f"Updated {updated_count} records with macro indicators")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error in macro indicators backfill: {e}")


if __name__ == "__main__":
    backfill_macro_indicators()




