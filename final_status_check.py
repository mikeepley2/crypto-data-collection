#!/usr/bin/env python3
"""
Final comprehensive status check
"""

import os
import mysql.connector


def final_status():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🎯 FINAL STATUS CHECK")
        print("=" * 50)

        # Today's records
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        total = cursor.fetchone()[0]
        print(f"📊 Today's Records: {total:,}")

        # Key coverage
        cursor.execute(
            "SELECT COUNT(avg_ml_overall_sentiment) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        sentiment = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(vix) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        vix = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(dxy) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        dxy = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(sma_20) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        technical = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(active_addresses_24h) FROM ml_features_materialized WHERE DATE(timestamp_iso) = CURDATE()"
        )
        onchain = cursor.fetchone()[0]

        print(f"\n📈 COVERAGE STATUS:")
        print(f"  • Sentiment: {sentiment:,} ({sentiment/total*100:.1f}%)")
        print(f"  • VIX: {vix:,} ({vix/total*100:.1f}%)")
        print(f"  • DXY: {dxy:,} ({dxy/total*100:.1f}%)")
        print(f"  • Technical: {technical:,} ({technical/total*100:.1f}%)")
        print(f"  • Onchain: {onchain:,} ({onchain/total*100:.1f}%)")

        # Sample record
        cursor.execute(
            """
            SELECT symbol, vix, dxy, sma_20, active_addresses_24h, avg_ml_overall_sentiment
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            LIMIT 1
        """
        )

        sample = cursor.fetchone()
        if sample:
            symbol, vix_val, dxy_val, sma_val, onchain_val, sentiment_val = sample
            print(f"\n🔍 SAMPLE RECORD ({symbol}):")
            print(f"  • VIX: {vix_val}")
            print(f"  • DXY: {dxy_val}")
            print(f"  • SMA20: {sma_val}")
            print(f"  • Onchain: {onchain_val}")
            print(f"  • Sentiment: {sentiment_val}")

        # Recent updates
        cursor.execute(
            """
            SELECT COUNT(*) FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND updated_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
        """
        )
        recent = cursor.fetchone()[0]
        print(f"\n🔄 Recent Updates (5 min): {recent:,}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    final_status()
