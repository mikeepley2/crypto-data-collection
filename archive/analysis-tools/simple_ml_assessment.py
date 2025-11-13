#!/usr/bin/env python3
"""
Simple ML Readiness Assessment
"""

import os
import mysql.connector


def simple_ml_assessment():
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

        # 7. CALCULATE OVERALL SCORE
        print("\nML READINESS SCORE")
        print("-" * 40)

        # Calculate coverage scores for each category
        price_coverage = 0
        for col in price_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            price_coverage += (count / total_records) * 100
        price_coverage = price_coverage / len(price_columns)

        sentiment_coverage = 0
        for col in sentiment_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            sentiment_coverage += (count / total_records) * 100
        sentiment_coverage = sentiment_coverage / len(sentiment_columns)

        tech_coverage = 0
        for col in tech_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            tech_coverage += (count / total_records) * 100
        tech_coverage = tech_coverage / len(tech_columns)

        onchain_coverage = 0
        for col in onchain_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            onchain_coverage += (count / total_records) * 100
        onchain_coverage = onchain_coverage / len(onchain_columns)

        macro_coverage = 0
        for col in macro_columns:
            cursor.execute(
                f"SELECT COUNT(*) FROM ml_features_materialized WHERE {col} IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            macro_coverage += (count / total_records) * 100
        macro_coverage = macro_coverage / len(macro_columns)

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

        # 8. RECOMMENDATIONS
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
    simple_ml_assessment()
