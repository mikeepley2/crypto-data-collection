#!/usr/bin/env python3
"""
Comprehensive ML Readiness Assessment for Materialized Table
"""

import os
import mysql.connector
from datetime import datetime, timedelta
import statistics


def assess_ml_readiness():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("=" * 80)
        print("ML READINESS ASSESSMENT - MATERIALIZED TABLE")
        print("=" * 80)

        # 1. OVERALL TABLE STATISTICS
        print("\nOVERALL TABLE STATISTICS")
        print("-" * 40)

        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]
        print(f"Total Records: {total_records:,}")

        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM ml_features_materialized")
        unique_symbols = cursor.fetchone()[0]
        print(f"Unique Symbols: {unique_symbols:,}")

        cursor.execute(
            "SELECT MIN(timestamp_iso), MAX(timestamp_iso) FROM ml_features_materialized"
        )
        date_range = cursor.fetchone()
        print(f"Date Range: {date_range[0]} to {date_range[1]}")

        # 2. PRICE DATA COVERAGE
        print("\nPRICE DATA COVERAGE")
        print("-" * 40)

        price_columns = [
            "current_price",
            "price_change_24h",
            "volume_24h",
            "market_cap",
        ]
        for col in price_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            coverage = (count / total_records) * 100
            print(f"{col:20}: {count:8,} ({coverage:5.1f}%)")

        # 3. SENTIMENT DATA COVERAGE
        print("\nSENTIMENT DATA COVERAGE")
        print("-" * 40)

        sentiment_columns = ["avg_ml_overall_sentiment", "sentiment_volume"]
        for col in sentiment_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            coverage = (count / total_records) * 100
            print(f"{col:25}: {count:8,} ({coverage:5.1f}%)")

        # 4. TECHNICAL INDICATORS COVERAGE
        print("\nTECHNICAL INDICATORS COVERAGE")
        print("-" * 40)

        tech_columns = [
            "sma_20",
            "rsi_14",
            "macd_line",
            "macd_signal",
            "macd_histogram",
            "bb_upper",
            "bb_middle",
            "bb_lower",
        ]
        for col in tech_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            coverage = (count / total_records) * 100
            print(f"{col:15}: {count:8,} ({coverage:5.1f}%)")

        # 5. ONCHAIN DATA COVERAGE
        print("\nONCHAIN DATA COVERAGE")
        print("-" * 40)

        onchain_columns = [
            "active_addresses_24h",
            "transaction_count_24h",
            "exchange_net_flow_24h",
            "price_volatility_7d",
        ]
        for col in onchain_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            coverage = (count / total_records) * 100
            print(f"{col:20}: {count:8,} ({coverage:5.1f}%)")

        # 6. MACRO INDICATORS COVERAGE
        print("\nMACRO INDICATORS COVERAGE")
        print("-" * 40)

        macro_columns = [
            "vix",
            "dxy",
            "treasury_10y",
            "unemployment_rate",
            "inflation_rate",
            "gold_price",
            "oil_price",
        ]
        for col in macro_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            coverage = (count / total_records) * 100
            print(f"{col:20}: {count:8,} ({coverage:5.1f}%)")

        # 7. DATA QUALITY ASSESSMENT
        print("\nDATA QUALITY ASSESSMENT")
        print("-" * 40)

        # Check for extreme outliers in price data
        cursor.execute(
            """
            SELECT 
                MIN(current_price) as min_price,
                MAX(current_price) as max_price,
                AVG(current_price) as avg_price,
                COUNT(CASE WHEN current_price <= 0 THEN 1 END) as zero_negative_prices
            FROM ml_features_materialized 
            WHERE current_price IS NOT NULL
        """
        )
        price_stats = cursor.fetchone()
        print(f"Price Range: ${price_stats[0]:,.2f} - ${price_stats[1]:,.2f}")
        print(f"Average Price: ${price_stats[2]:,.2f}")
        print(f"Zero/Negative Prices: {price_stats[3]:,}")

        # Check sentiment score distribution
        cursor.execute(
            """
            SELECT 
                MIN(avg_ml_overall_sentiment) as min_sentiment,
                MAX(avg_ml_overall_sentiment) as max_sentiment,
                AVG(avg_ml_overall_sentiment) as avg_sentiment,
                COUNT(CASE WHEN avg_ml_overall_sentiment < -1 OR avg_ml_overall_sentiment > 1 THEN 1 END) as outlier_sentiment
            FROM ml_features_materialized 
            WHERE avg_ml_overall_sentiment IS NOT NULL
        """
        )
        sentiment_stats = cursor.fetchone()
        if sentiment_stats[0] is not None:
            print(
                f"Sentiment Range: {sentiment_stats[0]:.3f} to {sentiment_stats[1]:.3f}"
            )
            print(f"Average Sentiment: {sentiment_stats[2]:.3f}")
            print(f"Outlier Sentiment Scores: {sentiment_stats[3]:,}")

        # 8. RECENT DATA COVERAGE (Last 7 days)
        print("\nRECENT DATA COVERAGE (Last 7 Days)")
        print("-" * 40)

        cursor.execute(
            """
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        )
        recent_records = cursor.fetchone()[0]
        print(f"Records (Last 7 days): {recent_records:,}")

        # Check recent sentiment coverage
        cursor.execute(
            """
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 7 DAY) 
            AND avg_ml_overall_sentiment IS NOT NULL
        """
        )
        recent_sentiment = cursor.fetchone()[0]
        recent_sentiment_pct = (
            (recent_sentiment / recent_records) * 100 if recent_records > 0 else 0
        )
        print(
            f"Recent Sentiment Coverage: {recent_sentiment:,} ({recent_sentiment_pct:.1f}%)"
        )

        # 9. ML READINESS SCORE
        print("\nML READINESS SCORE")
        print("-" * 40)

        # Calculate coverage scores for each category
        price_coverage = sum(
            [
                (
                    cursor.execute(
                        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
                    )
                    or cursor.fetchone()[0]
                )
                / total_records
                * 100
                for col in price_columns
            ]
        ) / len(price_columns)

        sentiment_coverage = sum(
            [
                (
                    cursor.execute(
                        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
                    )
                    or cursor.fetchone()[0]
                )
                / total_records
                * 100
                for col in sentiment_columns
            ]
        ) / len(sentiment_columns)

        tech_coverage = sum(
            [
                (
                    cursor.execute(
                        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
                    )
                    or cursor.fetchone()[0]
                )
                / total_records
                * 100
                for col in tech_columns
            ]
        ) / len(tech_columns)

        onchain_coverage = sum(
            [
                (
                    cursor.execute(
                        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
                    )
                    or cursor.fetchone()[0]
                )
                / total_records
                * 100
                for col in onchain_columns
            ]
        ) / len(onchain_columns)

        macro_coverage = sum(
            [
                (
                    cursor.execute(
                        f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
                    )
                    or cursor.fetchone()[0]
                )
                / total_records
                * 100
                for col in macro_columns
            ]
        ) / len(macro_columns)

        print(f"Price Data Coverage:     {price_coverage:5.1f}%")
        print(f"Sentiment Data Coverage: {sentiment_coverage:5.1f}%")
        print(f"Technical Data Coverage: {tech_coverage:5.1f}%")
        print(f"Onchain Data Coverage:   {onchain_coverage:5.1f}%")
        print(f"Macro Data Coverage:     {macro_coverage:5.1f}%")

        overall_score = (
            price_coverage
            + sentiment_coverage
            + tech_coverage
            + onchain_coverage
            + macro_coverage
        ) / 5
        print(f"\nOverall ML Readiness Score: {overall_score:.1f}%")

        # 10. RECOMMENDATIONS
        print("\nRECOMMENDATIONS")
        print("-" * 40)

        if overall_score >= 80:
            print("EXCELLENT: Ready for ML training with high-quality data")
        elif overall_score >= 60:
            print("GOOD: Ready for ML training with some data gaps")
        elif overall_score >= 40:
            print("FAIR: Consider data enhancement before ML training")
        else:
            print("POOR: Significant data gaps - not ready for ML training")

        if sentiment_coverage < 50:
            print("Priority: Improve sentiment data collection")
        if tech_coverage < 70:
            print("Priority: Enhance technical indicators calculation")
        if onchain_coverage < 50:
            print("Priority: Expand onchain data collection")
        if macro_coverage < 80:
            print("Priority: Ensure macro indicators are up-to-date")

        print("\n" + "=" * 80)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == "__main__":
    assess_ml_readiness()
