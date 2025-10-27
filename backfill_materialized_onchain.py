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


def backfill_materialized_onchain():
    """Backfill onchain data into materialized table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("🔄 Starting onchain data backfill for materialized table...")

        # Find records that need onchain data backfill
        cursor.execute(
            """
        SELECT 
            m.symbol,
            m.price_date,
            m.timestamp_iso,
            o.active_addresses_24h,
            o.transaction_count_24h,
            o.exchange_net_flow_24h,
            o.price_volatility_7d
        FROM ml_features_materialized m
        INNER JOIN crypto_onchain_data o ON m.symbol COLLATE utf8mb4_unicode_ci = o.coin_symbol COLLATE utf8mb4_unicode_ci
            AND DATE(m.price_date) = DATE(o.collection_date)
        WHERE m.active_addresses_24h IS NULL
        AND o.active_addresses_24h IS NOT NULL
        AND o.transaction_count_24h IS NOT NULL
        ORDER BY m.symbol, m.price_date
        LIMIT 10000
        """
        )

        records_to_update = cursor.fetchall()
        logger.info(f"Found {len(records_to_update)} records to backfill")

        if not records_to_update:
            logger.info("No records need onchain backfill")
            return 0

        updated_count = 0
        batch_size = 100

        for i in range(0, len(records_to_update), batch_size):
            batch = records_to_update[i : i + batch_size]

            for record in batch:
                (
                    symbol,
                    price_date,
                    timestamp_iso,
                    active_addresses,
                    transaction_count,
                    exchange_flow,
                    price_volatility,
                ) = record

                try:
                    # Update the materialized record with onchain data
                    cursor.execute(
                        """
                    UPDATE ml_features_materialized 
                    SET 
                        active_addresses_24h = %s,
                        transaction_count_24h = %s,
                        exchange_net_flow_24h = %s,
                        price_volatility_7d = %s,
                        updated_at = NOW()
                    WHERE symbol = %s 
                    AND price_date = %s
                    AND timestamp_iso = %s
                    """,
                        (
                            active_addresses,
                            transaction_count,
                            exchange_flow,
                            price_volatility,
                            symbol,
                            price_date,
                            timestamp_iso,
                        ),
                    )

                    updated_count += 1

                    if updated_count % 1000 == 0:
                        logger.info(f"Updated {updated_count} records...")

                except Exception as e:
                    logger.error(f"Error updating {symbol} {price_date}: {e}")
                    continue

            # Commit batch
            conn.commit()
            logger.info(
                f"Committed batch {i//batch_size + 1}, total updated: {updated_count}"
            )

        logger.info(f"✅ Onchain backfill completed: {updated_count} records updated")
        return updated_count

    except Exception as e:
        logger.error(f"❌ Error in onchain backfill: {e}")
        return 0
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


def check_backfill_results():
    """Check the results of the backfill"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("📊 Checking backfill results...")

        # Check updated coverage
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as has_active_addresses,
            SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as has_transaction_count,
            SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as has_exchange_flow,
            SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as has_price_volatility
        FROM ml_features_materialized
        """
        )

        coverage = cursor.fetchone()
        total = coverage[0]

        logger.info(f"📈 Updated Coverage:")
        logger.info(f"  Total records: {total:,}")
        logger.info(
            f"  Active Addresses: {coverage[1]:,} ({coverage[1]/total*100:.1f}%)"
        )
        logger.info(
            f"  Transaction Count: {coverage[2]:,} ({coverage[2]/total*100:.1f}%)"
        )
        logger.info(f"  Exchange Flow: {coverage[3]:,} ({coverage[3]/total*100:.1f}%)")
        logger.info(
            f"  Price Volatility: {coverage[4]:,} ({coverage[4]/total*100:.1f}%)"
        )

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error checking results: {e}")


if __name__ == "__main__":
    logger.info("🚀 Starting Materialized Table Onchain Backfill")

    # Run the backfill
    updated_count = backfill_materialized_onchain()

    if updated_count > 0:
        # Check results
        check_backfill_results()

    logger.info("✅ Onchain backfill process completed")
