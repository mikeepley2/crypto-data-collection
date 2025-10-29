#!/usr/bin/env python3
"""
Quick data status check for materialized table
"""

import os
import mysql.connector
from datetime import datetime


def check_data_status():
    """Check current data coverage status"""

    # Database connection
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "news_collector"),
        password=os.getenv("DB_PASSWORD", "99Rules!"),
        database=os.getenv("DB_NAME", "crypto_prices"),
    )

    try:
        cursor = conn.cursor()

        print("🔍 CURRENT DATA STATUS CHECK")
        print("=" * 50)

        # Total records
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_records = cursor.fetchone()[0]
        print(f"📊 Total Records: {total_records:,}")

        # Sentiment coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(avg_ml_overall_sentiment) as with_sentiment,
                ROUND(COUNT(avg_ml_overall_sentiment) * 100.0 / COUNT(*), 1) as percentage
            FROM ml_features_materialized
        """
        )
        sentiment_stats = cursor.fetchone()
        print(
            f"💭 Sentiment Coverage: {sentiment_stats[1]:,}/{sentiment_stats[0]:,} ({sentiment_stats[2]}%)"
        )

        # Close price coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(close_price) as with_close_price,
                ROUND(COUNT(close_price) * 100.0 / COUNT(*), 1) as percentage
            FROM ml_features_materialized
        """
        )
        close_stats = cursor.fetchone()
        print(
            f"💰 Close Price Coverage: {close_stats[1]:,}/{close_stats[0]:,} ({close_stats[2]}%)"
        )

        # Onchain coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(active_addresses_24h) as with_onchain,
                ROUND(COUNT(active_addresses_24h) * 100.0 / COUNT(*), 1) as percentage
            FROM ml_features_materialized
        """
        )
        onchain_stats = cursor.fetchone()
        print(
            f"⛓️ Onchain Coverage: {onchain_stats[1]:,}/{onchain_stats[0]:,} ({onchain_stats[2]}%)"
        )

        # Technical indicators coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(sma_20) as with_technical,
                ROUND(COUNT(sma_20) * 100.0 / COUNT(*), 1) as percentage
            FROM ml_features_materialized
        """
        )
        tech_stats = cursor.fetchone()
        print(
            f"📈 Technical Coverage: {tech_stats[1]:,}/{tech_stats[0]:,} ({tech_stats[2]}%)"
        )

        # Macro coverage
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(vix) as with_macro,
                ROUND(COUNT(vix) * 100.0 / COUNT(*), 1) as percentage
            FROM ml_features_materialized
        """
        )
        macro_stats = cursor.fetchone()
        print(
            f"🌍 Macro Coverage: {macro_stats[1]:,}/{macro_stats[0]:,} ({macro_stats[2]}%)"
        )

        # Recent updates (last 10 minutes)
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        """
        )
        recent_updates = cursor.fetchone()[0]
        print(f"🔄 Recent Updates (10m): {recent_updates:,}")

        print("\n🎯 TARGETS:")
        print("• Sentiment: 80%+ (currently {})".format(sentiment_stats[2]))
        print("• Onchain: 90%+ (currently {})".format(onchain_stats[2]))
        print("• Technical: 95%+ (currently {})".format(tech_stats[2]))
        print("• Macro: 95%+ (currently {})".format(macro_stats[2]))
        print("• Close Prices: 95%+ (currently {})".format(close_stats[2]))

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_data_status()
