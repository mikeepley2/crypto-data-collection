#!/usr/bin/env python3
"""
Check column coverage for today's records
"""

import os
import mysql.connector
from datetime import datetime


def check_today_coverage():
    """Check column coverage for today's records"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 TODAY'S RECORDS COLUMN COVERAGE")
        print("=" * 50)

        # Get today's records
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
        """
        )
        today_total = cursor.fetchone()[0]
        print(f"📊 Today's Records: {today_total:,}")

        if today_total == 0:
            print("❌ No records for today")
            return

        # Check each column coverage for today
        columns_to_check = [
            ("current_price", "💰 Current Price"),
            ("price_change_24h", "📈 Price Change 24h"),
            ("volume_24h", "📊 Volume 24h"),
            ("market_cap", "🏦 Market Cap"),
            ("avg_ml_overall_sentiment", "💭 ML Sentiment"),
            ("sentiment_volume", "📝 Sentiment Volume"),
            ("active_addresses_24h", "⛓️ Active Addresses"),
            ("transaction_count_24h", "🔄 Transaction Count"),
            ("exchange_net_flow_24h", "💸 Exchange Net Flow"),
            ("price_volatility_7d", "📊 Price Volatility"),
            ("sma_20", "📈 SMA 20"),
            ("rsi_14", "📊 RSI 14"),
            ("macd_line", "📈 MACD Line"),
            ("macd_signal", "📊 MACD Signal"),
            ("macd_histogram", "📈 MACD Histogram"),
            ("bb_upper", "📊 Bollinger Upper"),
            ("bb_middle", "📊 Bollinger Middle"),
            ("bb_lower", "📊 Bollinger Lower"),
            ("vix", "🌍 VIX"),
            ("spx", "📈 S&P 500"),
            ("dxy", "💵 DXY"),
            ("treasury_10y", "🏛️ Treasury 10Y"),
            ("unemployment_rate", "👥 Unemployment"),
            ("inflation_rate", "📈 Inflation"),
            ("gold_price", "🥇 Gold Price"),
            ("oil_price", "🛢️ Oil Price"),
            ("close_price", "💰 Close Price"),
            ("close", "💰 Close"),
        ]

        print(f"\n📋 COLUMN COVERAGE FOR TODAY'S RECORDS:")
        print("-" * 50)

        for column, description in columns_to_check:
            cursor.execute(
                f"""
                SELECT COUNT({column}) 
                FROM ml_features_materialized 
                WHERE DATE(timestamp_iso) = CURDATE()
            """
            )
            count = cursor.fetchone()[0]
            percentage = round(count * 100.0 / today_total, 1)

            status = "✅" if percentage >= 90 else "⚠️" if percentage >= 50 else "❌"
            print(f"{status} {description}: {count:,}/{today_total:,} ({percentage}%)")

        # Check recent updates
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        )
        recent_1h = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        """
        )
        recent_10m = cursor.fetchone()[0]

        print(f"\n🔄 RECENT ACTIVITY:")
        print(f"• Updated in last 1 hour: {recent_1h:,}")
        print(f"• Updated in last 10 minutes: {recent_10m:,}")

        # Check data quality for key columns
        print(f"\n🎯 DATA QUALITY CHECK:")

        # Check sentiment range
        cursor.execute(
            """
            SELECT MIN(avg_ml_overall_sentiment), MAX(avg_ml_overall_sentiment), AVG(avg_ml_overall_sentiment)
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND avg_ml_overall_sentiment IS NOT NULL
        """
        )
        sentiment_stats = cursor.fetchone()
        if sentiment_stats[0] is not None:
            print(
                f"• Sentiment Range: {sentiment_stats[0]:.3f} to {sentiment_stats[2]:.3f} (avg: {sentiment_stats[2]:.3f})"
            )

        # Check price range
        cursor.execute(
            """
            SELECT MIN(current_price), MAX(current_price), AVG(current_price)
            FROM ml_features_materialized 
            WHERE DATE(timestamp_iso) = CURDATE()
            AND current_price IS NOT NULL
        """
        )
        price_stats = cursor.fetchone()
        if price_stats[0] is not None:
            print(
                f"• Price Range: ${price_stats[0]:.2f} to ${price_stats[2]:.2f} (avg: ${price_stats[2]:.2f})"
            )

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_today_coverage()
