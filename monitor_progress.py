#!/usr/bin/env python3
"""
Monitor system progress and data coverage improvements
"""

import os
import mysql.connector
import time
from datetime import datetime


def check_progress():
    """Check current progress and show improvements"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        # Get current timestamp
        now = datetime.now().strftime("%H:%M:%S")

        print(f"\n🕐 {now} - SYSTEM PROGRESS MONITOR")
        print("=" * 50)

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
            "SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)"
        )
        recent_5m = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM ml_features_materialized WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)"
        )
        recent_10m = cursor.fetchone()[0]
        print(f"🔄 Recent Updates: {recent_5m:,} (5m) | {recent_10m:,} (10m)")

        # Calculate progress towards targets
        sentiment_progress = min(sentiment_pct / 80.0 * 100, 100)
        close_progress = min(close_pct / 95.0 * 100, 100)
        onchain_progress = min(onchain_pct / 90.0 * 100, 100)
        tech_progress = min(tech_pct / 95.0 * 100, 100)

        print(f"\n🎯 Progress Towards Targets:")
        print(f"• Sentiment: {sentiment_progress:.1f}% (target: 80%)")
        print(f"• Close Price: {close_progress:.1f}% (target: 95%)")
        print(f"• Onchain: {onchain_progress:.1f}% (target: 90%)")
        print(f"• Technical: {tech_progress:.1f}% (target: 95%)")

        return {
            "total": total,
            "sentiment": sentiment,
            "sentiment_pct": sentiment_pct,
            "close": close,
            "close_pct": close_pct,
            "onchain": onchain,
            "onchain_pct": onchain_pct,
            "tech": tech,
            "tech_pct": tech_pct,
            "recent_5m": recent_5m,
            "recent_10m": recent_10m,
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def monitor_loop():
    """Monitor progress in a loop"""
    print("🚀 Starting Progress Monitor")
    print("Press Ctrl+C to stop")

    # Initial baseline
    baseline = check_progress()
    if not baseline:
        return

    print(f"\n📈 Monitoring changes from baseline...")
    print("=" * 50)

    try:
        while True:
            time.sleep(60)  # Check every minute

            current = check_progress()
            if not current:
                continue

            # Calculate changes
            total_change = current["total"] - baseline["total"]
            sentiment_change = current["sentiment"] - baseline["sentiment"]
            close_change = current["close"] - baseline["close"]
            onchain_change = current["onchain"] - baseline["onchain"]
            tech_change = current["tech"] - baseline["tech"]

            print(f"\n📊 CHANGES SINCE BASELINE:")
            print(f"• Total Records: {total_change:+,}")
            print(
                f"• Sentiment: {sentiment_change:+,} ({current['sentiment_pct'] - baseline['sentiment_pct']:+.1f}%)"
            )
            print(
                f"• Close Price: {close_change:+,} ({current['close_pct'] - baseline['close_pct']:+.1f}%)"
            )
            print(
                f"• Onchain: {onchain_change:+,} ({current['onchain_pct'] - baseline['onchain_pct']:+.1f}%)"
            )
            print(
                f"• Technical: {tech_change:+,} ({current['tech_pct'] - baseline['tech_pct']:+.1f}%)"
            )

            # Update baseline every 5 minutes
            if int(time.time()) % 300 == 0:
                baseline = current
                print(f"\n🔄 Updated baseline at {datetime.now().strftime('%H:%M:%S')}")

    except KeyboardInterrupt:
        print(f"\n\n✅ Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")
        print("Final status:")
        check_progress()


if __name__ == "__main__":
    monitor_loop()
