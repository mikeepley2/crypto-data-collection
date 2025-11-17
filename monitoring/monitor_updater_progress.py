#!/usr/bin/env python3
"""Monitor materialized updater progress every 5 minutes"""
import mysql.connector
import time
from datetime import datetime, timedelta
import os
import sys


def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="news_collector",
            password="99Rules!",
            database="crypto_prices",
            connect_timeout=5,
        )
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def check_progress():
    """Check current progress"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)

        # Get recent activity
        cursor.execute(
            """
            SELECT 
                MAX(updated_at) as last_update,
                MAX(timestamp_iso) as latest_timestamp,
                COUNT(CASE WHEN updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE) THEN 1 END) as updated_last_10min
            FROM ml_features_materialized
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """
        )
        activity = cursor.fetchone()

        # Check completeness for key columns (last 24 hours)
        columns_to_check = [
            ("rsi_14", "Technical"),
            ("sma_20", "Technical"),
            ("vix", "Macro"),
            ("spx", "Macro"),
            ("open_price", "OHLC"),
            ("high_price", "OHLC"),
            ("active_addresses_24h", "Onchain"),
            ("transaction_count_24h", "Onchain"),
        ]

        completeness = {}
        for col, category in columns_to_check:
            try:
                cursor.execute(
                    f"""
                    SELECT 
                        COUNT({col}) as filled,
                        COUNT(*) as total,
                        ROUND(COUNT({col}) * 100.0 / COUNT(*), 1) as pct
                    FROM ml_features_materialized
                    WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                """
                )
                result = cursor.fetchone()
                completeness[col] = {
                    "category": category,
                    "filled": result["filled"],
                    "total": result["total"],
                    "pct": result["pct"],
                }
            except Exception as e:
                completeness[col] = {
                    "category": category,
                    "filled": 0,
                    "total": 0,
                    "pct": 0,
                    "error": str(e),
                }

        cursor.close()
        conn.close()

        return {
            "activity": activity,
            "completeness": completeness,
        }
    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        if conn:
            conn.close()
        return None


def print_progress(stats, iteration):
    """Print progress in a formatted way"""
    # Clear screen (works on Windows and Unix)
    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 80)
    print(f"MATERIALIZED UPDATER PROGRESS MONITOR - Check #{iteration}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    if not stats:
        print("❌ Could not retrieve stats")
        return

    # Activity status
    activity = stats.get("activity", {})
    print("📊 Recent Activity (Last 24 hours):")
    print(f"   Last update: {activity.get('last_update', 'N/A')}")
    print(f"   Latest timestamp: {activity.get('latest_timestamp', 'N/A')}")
    print(
        f"   Updated in last 10 min: {activity.get('updated_last_10min', 0):,} records"
    )
    print()

    # Completeness by category
    completeness = stats.get("completeness", {})

    categories = {}
    for col, data in completeness.items():
        cat = data.get("category", "Unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((col, data))

    print("📈 Column Completeness (Last 24 hours):")
    print("-" * 80)

    for category in ["Technical", "Macro", "OHLC", "Onchain"]:
        if category in categories:
            print(f"\n{category} Indicators:")
            for col, data in categories[category]:
                pct = data.get("pct", 0)
                filled = data.get("filled", 0)
                total = data.get("total", 0)

                status = "✅" if pct >= 50 else "⚠️" if pct > 0 else "❌"
                bar_length = int(pct / 2)  # Scale to 50 chars max
                bar = "█" * bar_length + "░" * (50 - bar_length)

                print(
                    f"   {status} {col:25} {bar} {pct:>5.1f}% ({filled:>8,}/{total:>8,})"
                )

    print()
    print("-" * 80)
    print(f"⏱️  Next check in 5 minutes... (Press Ctrl+C to stop)")
    print("=" * 80)


def main():
    """Main monitoring loop"""
    print("Starting Materialized Updater Progress Monitor")
    print("Checking every 5 minutes...")
    print("Press Ctrl+C to stop")
    print()

    iteration = 0
    baseline_stats = None

    try:
        while True:
            iteration += 1
            stats = check_progress()

            if stats:
                if iteration == 1:
                    baseline_stats = stats.copy()
                    print_progress(stats, iteration)
                else:
                    print_progress(stats, iteration)

                    # Show improvements since baseline
                    if baseline_stats:
                        print("\n📊 Progress Since Start:")
                        baseline_comp = baseline_stats.get("completeness", {})
                        current_comp = stats.get("completeness", {})

                        improvements = []
                        for col in current_comp:
                            if col in baseline_comp:
                                baseline_pct = baseline_comp[col].get("pct", 0)
                                current_pct = current_comp[col].get("pct", 0)
                                diff = current_pct - baseline_pct
                                if diff > 0.1:  # Only show if significant improvement
                                    improvements.append(
                                        (col, baseline_pct, current_pct, diff)
                                    )

                        if improvements:
                            for col, baseline, current, diff in improvements:
                                print(
                                    f"   ✅ {col:25} {baseline:>5.1f}% → {current:>5.1f}% (+{diff:>5.1f}%)"
                                )
                        else:
                            print(
                                "   (No significant changes yet - wait for new data to process)"
                            )
                        print()
            else:
                print(f"❌ Check #{iteration} failed - retrying in 5 minutes...")

            # Wait 5 minutes (300 seconds)
            time.sleep(300)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print("Final stats:")
        if stats:
            print_progress(stats, iteration)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error in monitoring loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

