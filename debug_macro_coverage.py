#!/usr/bin/env python3
"""
Debug macro data coverage specifically
"""

import os
import mysql.connector


def debug_macro_coverage():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 MACRO DATA COVERAGE DEBUG")
        print("=" * 50)

        # Check today's records with macro data
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
        """
        )
        today_total = cursor.fetchone()[0]
        print(f"📊 Today's Total Records: {today_total:,}")

        # Check each macro column specifically
        macro_columns = [
            "vix",
            "dxy",
            "treasury_10y",
            "unemployment_rate",
            "inflation_rate",
            "gold_price",
            "oil_price",
        ]

        print(f"\n🌍 MACRO COLUMN COVERAGE:")
        for column in macro_columns:
            cursor.execute(
                f"""
                SELECT COUNT({column}) 
                FROM ml_features_materialized 
                WHERE DATE(timestamp_iso) = CURDATE()
                AND {column} IS NOT NULL
            """
            )
            count = cursor.fetchone()[0]
            percentage = round(count * 100.0 / today_total, 1) if today_total > 0 else 0
            print(f"  • {column}: {count:,}/{today_total:,} ({percentage}%)")

        # Check if any macro data exists at all
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND (vix IS NOT NULL OR dxy IS NOT NULL OR treasury_10y IS NOT NULL 
                 OR unemployment_rate IS NOT NULL OR inflation_rate IS NOT NULL 
                 OR gold_price IS NOT NULL OR oil_price IS NOT NULL)
        """
        )
        any_macro = cursor.fetchone()[0]
        print(f"\n📈 Records with ANY macro data: {any_macro:,}/{today_total:,}")

        # Check sample records
        cursor.execute(
            """
            SELECT symbol, vix, dxy, treasury_10y, unemployment_rate, inflation_rate, gold_price, oil_price
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            LIMIT 5
        """
        )

        samples = cursor.fetchall()
        print(f"\n🔍 SAMPLE RECORDS:")
        for i, sample in enumerate(samples, 1):
            symbol = sample[0]
            macro_values = sample[1:]
            non_null_count = sum(1 for v in macro_values if v is not None)
            print(f"  {i}. {symbol}: {non_null_count}/7 macro values populated")
            print(f"     VIX: {sample[1]}, DXY: {sample[2]}, Treasury: {sample[3]}")
            print(f"     Unemployment: {sample[4]}, Inflation: {sample[5]}")
            print(f"     Gold: {sample[6]}, Oil: {sample[7]}")

        # Check recent updates
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        """
        )
        recent_updates = cursor.fetchone()[0]
        print(f"\n🔄 Recent Updates (10 min): {recent_updates:,}")

        # Check if materialized updater is actually updating records
        cursor.execute(
            """
            SELECT symbol, updated_at, vix, dxy
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            ORDER BY updated_at DESC
            LIMIT 3
        """
        )

        recent_records = cursor.fetchall()
        print(f"\n⏰ MOST RECENTLY UPDATED RECORDS:")
        for symbol, updated_at, vix, dxy in recent_records:
            print(f"  • {symbol}: Updated {updated_at}, VIX={vix}, DXY={dxy}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    debug_macro_coverage()
