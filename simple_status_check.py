#!/usr/bin/env python3
"""
Simple status check for materialized table
"""

import os
import mysql.connector


def check_status():
    """Quick status check"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 QUICK STATUS CHECK")
        print("=" * 30)

        # Total records
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total = cursor.fetchone()[0]
        print(f"📊 Total Records: {total:,}")

        # Sentiment coverage
        cursor.execute(
            "SELECT COUNT(avg_ml_overall_sentiment) FROM ml_features_materialized"
        )
        sentiment = cursor.fetchone()[0]
        sentiment_pct = round(sentiment * 100.0 / total, 1)
        print(f"💭 Sentiment: {sentiment:,} ({sentiment_pct}%)")

        # Close price coverage
        cursor.execute("SELECT COUNT(close_price) FROM ml_features_materialized")
        close = cursor.fetchone()[0]
        close_pct = round(close * 100.0 / total, 1)
        print(f"💰 Close Price: {close:,} ({close_pct}%)")

        # Onchain coverage
        cursor.execute(
            "SELECT COUNT(active_addresses_24h) FROM ml_features_materialized"
        )
        onchain = cursor.fetchone()[0]
        onchain_pct = round(onchain * 100.0 / total, 1)
        print(f"⛓️ Onchain: {onchain:,} ({onchain_pct}%)")

        # Technical coverage
        cursor.execute("SELECT COUNT(sma_20) FROM ml_features_materialized")
        tech = cursor.fetchone()[0]
        tech_pct = round(tech * 100.0 / total, 1)
        print(f"📈 Technical: {tech:,} ({tech_pct}%)")

        # Recent updates
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)"
        )
        recent = cursor.fetchone()[0]
        print(f"🔄 Recent (10m): {recent:,}")

        print(f"\n🎯 Progress:")
        print(f"• Sentiment: {sentiment_pct}% (target: 80%+)")
        print(f"• Close Price: {close_pct}% (target: 95%+)")
        print(f"• Onchain: {onchain_pct}% (target: 90%+)")
        print(f"• Technical: {tech_pct}% (target: 95%+)")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_status()
