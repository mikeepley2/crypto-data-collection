#!/usr/bin/env python3
"""
Comprehensive Materialized Table Validation
Validates all columns in ml_features_materialized for completeness
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


def validate_materialized_table_completeness():
    """Validate all columns in materialized table for completeness"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        print("=" * 80)
        print("COMPREHENSIVE MATERIALIZED TABLE VALIDATION")
        print("=" * 80)
        print()

        # 1. Get table schema
        print("1. TABLE SCHEMA ANALYSIS")
        print("-" * 50)
        cursor.execute("DESCRIBE ml_features_materialized")
        schema = cursor.fetchall()

        print("Columns in ml_features_materialized:")
        for col in schema:
            print(
                f"  {col['Field']}: {col['Type']} {'NULL' if col['Null'] == 'YES' else 'NOT NULL'}"
            )

        print()

        # 2. Overall record count and date range
        print("2. OVERALL TABLE STATISTICS")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_records,
                MIN(price_date) as earliest_date,
                MAX(price_date) as latest_date,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(DISTINCT price_date) as unique_dates
            FROM ml_features_materialized
        """
        )
        stats = cursor.fetchone()

        print(f"Total records: {stats['total_records']:,}")
        print(f"Date range: {stats['earliest_date']} to {stats['latest_date']}")
        print(f"Unique symbols: {stats['unique_symbols']}")
        print(f"Unique dates: {stats['unique_dates']}")
        print()

        # 3. Price data coverage
        print("3. PRICE DATA COVERAGE")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN current_price IS NOT NULL THEN 1 ELSE 0 END) as has_current_price,
                SUM(CASE WHEN price_change_24h IS NOT NULL THEN 1 ELSE 0 END) as has_price_change,
                SUM(CASE WHEN volume_24h IS NOT NULL THEN 1 ELSE 0 END) as has_volume,
                SUM(CASE WHEN market_cap IS NOT NULL THEN 1 ELSE 0 END) as has_market_cap
            FROM ml_features_materialized
        """
        )
        price_coverage = cursor.fetchone()
        total = price_coverage["total_records"]

        print(
            f"Current Price: {price_coverage['has_current_price']:,} ({price_coverage['has_current_price']/total*100:.1f}%)"
        )
        print(
            f"Price Change 24h: {price_coverage['has_price_change']:,} ({price_coverage['has_price_change']/total*100:.1f}%)"
        )
        print(
            f"Volume 24h: {price_coverage['has_volume']:,} ({price_coverage['has_volume']/total*100:.1f}%)"
        )
        print(
            f"Market Cap: {price_coverage['has_market_cap']:,} ({price_coverage['has_market_cap']/total*100:.1f}%)"
        )
        print()

        # 4. Sentiment data coverage
        print("4. SENTIMENT DATA COVERAGE")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                SUM(CASE WHEN avg_ml_crypto_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_crypto_sentiment,
                SUM(CASE WHEN avg_ml_stock_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_stock_sentiment,
                SUM(CASE WHEN avg_ml_social_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social_sentiment,
                SUM(CASE WHEN avg_ml_overall_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_overall_sentiment,
                SUM(CASE WHEN sentiment_volume IS NOT NULL THEN 1 ELSE 0 END) as has_sentiment_volume
            FROM ml_features_materialized
        """
        )
        sentiment_coverage = cursor.fetchone()

        print(
            f"Crypto Sentiment: {sentiment_coverage['has_crypto_sentiment']:,} ({sentiment_coverage['has_crypto_sentiment']/total*100:.1f}%)"
        )
        print(
            f"Stock Sentiment: {sentiment_coverage['has_stock_sentiment']:,} ({sentiment_coverage['has_stock_sentiment']/total*100:.1f}%)"
        )
        print(
            f"Social Sentiment: {sentiment_coverage['has_social_sentiment']:,} ({sentiment_coverage['has_social_sentiment']/total*100:.1f}%)"
        )
        print(
            f"Overall Sentiment: {sentiment_coverage['has_overall_sentiment']:,} ({sentiment_coverage['has_overall_sentiment']/total*100:.1f}%)"
        )
        print(
            f"Sentiment Volume: {sentiment_coverage['has_sentiment_volume']:,} ({sentiment_coverage['has_sentiment_volume']/total*100:.1f}%)"
        )
        print()

        # 5. Onchain data coverage
        print("5. ONCHAIN DATA COVERAGE")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as has_active_addresses,
                SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as has_transaction_count,
                SUM(CASE WHEN exchange_net_flow_24h IS NOT NULL THEN 1 ELSE 0 END) as has_exchange_flow,
                SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as has_price_volatility
            FROM ml_features_materialized
        """
        )
        onchain_coverage = cursor.fetchone()

        print(
            f"Active Addresses 24h: {onchain_coverage['has_active_addresses']:,} ({onchain_coverage['has_active_addresses']/total*100:.1f}%)"
        )
        print(
            f"Transaction Count 24h: {onchain_coverage['has_transaction_count']:,} ({onchain_coverage['has_transaction_count']/total*100:.1f}%)"
        )
        print(
            f"Exchange Net Flow 24h: {onchain_coverage['has_exchange_flow']:,} ({onchain_coverage['has_exchange_flow']/total*100:.1f}%)"
        )
        print(
            f"Price Volatility 7d: {onchain_coverage['has_price_volatility']:,} ({onchain_coverage['has_price_volatility']/total*100:.1f}%)"
        )
        print()

        # 6. Complete records analysis
        print("6. COMPLETE RECORDS ANALYSIS")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN current_price IS NOT NULL 
                    AND avg_ml_overall_sentiment IS NOT NULL 
                    AND active_addresses_24h IS NOT NULL 
                    THEN 1 ELSE 0 END) as complete_records,
                SUM(CASE WHEN current_price IS NOT NULL 
                    AND avg_ml_overall_sentiment IS NOT NULL 
                    AND active_addresses_24h IS NOT NULL 
                    AND transaction_count_24h IS NOT NULL 
                    AND exchange_net_flow_24h IS NOT NULL 
                    AND price_volatility_7d IS NOT NULL 
                    THEN 1 ELSE 0 END) as fully_complete_records
            FROM ml_features_materialized
        """
        )
        complete_analysis = cursor.fetchone()

        print(
            f"Records with Price + Sentiment + Onchain: {complete_analysis['complete_records']:,} ({complete_analysis['complete_records']/total*100:.1f}%)"
        )
        print(
            f"Fully Complete Records (all fields): {complete_analysis['fully_complete_records']:,} ({complete_analysis['fully_complete_records']/total*100:.1f}%)"
        )
        print()

        # 7. Recent data freshness
        print("7. RECENT DATA FRESHNESS")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                COUNT(*) as recent_records,
                MAX(updated_at) as latest_update,
                COUNT(DISTINCT symbol) as recent_symbols
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        )
        recent_data = cursor.fetchone()

        print(f"Records updated in last hour: {recent_data['recent_records']:,}")
        print(f"Latest update: {recent_data['latest_update']}")
        print(f"Symbols updated recently: {recent_data['recent_symbols']}")
        print()

        # 8. Sample complete records
        print("8. SAMPLE COMPLETE RECORDS")
        print("-" * 50)
        cursor.execute(
            """
            SELECT 
                symbol, price_date, current_price, avg_ml_overall_sentiment,
                active_addresses_24h, transaction_count_24h, price_volatility_7d,
                updated_at
            FROM ml_features_materialized 
            WHERE current_price IS NOT NULL 
            AND avg_ml_overall_sentiment IS NOT NULL 
            AND active_addresses_24h IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 5
        """
        )
        sample_records = cursor.fetchall()

        print("Sample complete records:")
        for record in sample_records:
            print(
                f"  {record['symbol']} ({record['price_date']}): "
                f"price=${record['current_price']:.2f}, "
                f"sentiment={record['avg_ml_overall_sentiment']:.3f}, "
                f"active={record['active_addresses_24h']:,}, "
                f"volatility={record['price_volatility_7d']:.2f}%"
            )
        print()

        # 9. Data quality summary
        print("9. DATA QUALITY SUMMARY")
        print("-" * 50)

        # Calculate overall completeness score
        price_score = (
            (
                price_coverage["has_current_price"]
                + price_coverage["has_price_change"]
                + price_coverage["has_volume"]
                + price_coverage["has_market_cap"]
            )
            / (4 * total)
            * 100
        )

        sentiment_score = (
            (
                sentiment_coverage["has_crypto_sentiment"]
                + sentiment_coverage["has_stock_sentiment"]
                + sentiment_coverage["has_social_sentiment"]
                + sentiment_coverage["has_overall_sentiment"]
                + sentiment_coverage["has_sentiment_volume"]
            )
            / (5 * total)
            * 100
        )

        onchain_score = (
            (
                onchain_coverage["has_active_addresses"]
                + onchain_coverage["has_transaction_count"]
                + onchain_coverage["has_exchange_flow"]
                + onchain_coverage["has_price_volatility"]
            )
            / (4 * total)
            * 100
        )

        overall_score = (price_score + sentiment_score + onchain_score) / 3

        print(f"Price Data Completeness: {price_score:.1f}%")
        print(f"Sentiment Data Completeness: {sentiment_score:.1f}%")
        print(f"Onchain Data Completeness: {onchain_score:.1f}%")
        print(f"Overall Data Completeness: {overall_score:.1f}%")
        print()

        # 10. Recommendations
        print("10. RECOMMENDATIONS")
        print("-" * 50)

        if price_score < 95:
            print("[WARN] Price data coverage could be improved")
        if sentiment_score < 80:
            print("[WARN] Sentiment data coverage could be improved")
        if onchain_score < 50:
            print("[WARN] Onchain data coverage needs significant improvement")
        if overall_score < 70:
            print("[WARN] Overall data completeness needs attention")

        if price_score >= 95 and sentiment_score >= 80 and onchain_score >= 50:
            print("[OK] All data categories have good coverage!")

        print()
        print("=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error during validation: {e}")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    validate_materialized_table_completeness()
