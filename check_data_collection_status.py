#!/usr/bin/env python3
"""
Check current data collection status across all services
"""

import mysql.connector
import os
from datetime import datetime, timedelta


def check_data_collection_status():
    """Check what data is currently being collected"""

    # Database connection
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "host.docker.internal"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "news_collector"),
        password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
        database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
    )

    cursor = conn.cursor()

    print("📊 CURRENT DATA COLLECTION STATUS")
    print("=" * 50)

    try:
        # Check price data
        cursor.execute(
            "SELECT COUNT(*) FROM price_data_real WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)"
        )
        price_count = cursor.fetchone()[0]
        print(f"💰 Price Data (last hour): {price_count:,} records")

        # Check news data
        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)"
        )
        news_count = cursor.fetchone()[0]
        print(f"📰 News Data (last hour): {news_count:,} records")

        # Check sentiment data
        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE sentiment_score IS NOT NULL AND sentiment_processed_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)"
        )
        sentiment_count = cursor.fetchone()[0]
        print(f"🧠 Sentiment Data (last hour): {sentiment_count:,} records")

        # Check total records
        cursor.execute("SELECT COUNT(*) FROM price_data_real")
        total_prices = cursor.fetchone()[0]
        print(f"💰 Total Price Records: {total_prices:,}")

        cursor.execute("SELECT COUNT(*) FROM crypto_news")
        total_news = cursor.fetchone()[0]
        print(f"📰 Total News Records: {total_news:,}")

        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE sentiment_score IS NOT NULL"
        )
        total_sentiment = cursor.fetchone()[0]
        print(f"🧠 Total Sentiment Records: {total_sentiment:,}")

        # Check if there are any onchain/macro/technical tables
        cursor.execute("SHOW TABLES")
        all_tables = cursor.fetchall()

        onchain_tables = [t[0] for t in all_tables if "onchain" in t[0].lower()]
        macro_tables = [t[0] for t in all_tables if "macro" in t[0].lower()]
        technical_tables = [t[0] for t in all_tables if "technical" in t[0].lower()]

        print(f"\n🔗 Data Collection Coverage:")
        print(f"   - Onchain Data Tables: {len(onchain_tables)} found")
        if onchain_tables:
            for table in onchain_tables:
                print(f"     * {table}")

        print(f"   - Macro Data Tables: {len(macro_tables)} found")
        if macro_tables:
            for table in macro_tables:
                print(f"     * {table}")

        print(f"   - Technical Data Tables: {len(technical_tables)} found")
        if technical_tables:
            for table in technical_tables:
                print(f"     * {table}")

        if not onchain_tables and not macro_tables and not technical_tables:
            print("⚠️  No onchain/macro/technical data tables found")
            print("   Only price, news, and sentiment data is being collected")

        # Check recent activity
        print(f"\n⏰ Recent Activity (last 24 hours):")
        cursor.execute(
            "SELECT COUNT(*) FROM price_data_real WHERE timestamp > DATE_SUB(NOW(), INTERVAL 24 HOUR)"
        )
        recent_prices = cursor.fetchone()[0]
        print(f"   - Price updates: {recent_prices:,}")

        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)"
        )
        recent_news = cursor.fetchone()[0]
        print(f"   - News articles: {recent_news:,}")

        cursor.execute(
            "SELECT COUNT(*) FROM crypto_news WHERE sentiment_processed_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)"
        )
        recent_sentiment = cursor.fetchone()[0]
        print(f"   - Sentiment analyses: {recent_sentiment:,}")

    except Exception as e:
        print(f"❌ Error checking data: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    check_data_collection_status()




