#!/usr/bin/env python3
"""
ML Features Monitoring - Windows Compatible
Monitors materialized ML features without Unicode symbols
"""

import pymysql
import time
from datetime import datetime, timedelta
import sys

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
    "charset": "utf8mb4",
    "autocommit": True,
}


def get_connection():
    """Get database connection"""
    return pymysql.connect(**DB_CONFIG)


def get_ml_features_status():
    """Get ML features status"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Overall stats
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MAX(timestamp_iso) as latest_data,
                    MAX(updated_at) as latest_update
                FROM ml_features_materialized
            """
            )
            overall = cursor.fetchone()

            # Recent activity
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as updates_1h,
                    COUNT(DISTINCT symbol) as symbols_1h
                FROM ml_features_materialized
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
            )
            recent_1h = cursor.fetchone()

            cursor.execute(
                """
                SELECT 
                    COUNT(*) as updates_10m,
                    COUNT(DISTINCT symbol) as symbols_10m
                FROM ml_features_materialized
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            """
            )
            recent_10m = cursor.fetchone()

            # Recent samples
            cursor.execute(
                """
                SELECT symbol, timestamp_iso, updated_at
                FROM ml_features_materialized
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)
                ORDER BY updated_at DESC
                LIMIT 5
            """
            )
            samples = cursor.fetchall()

            return {
                "overall": overall,
                "recent_1h": recent_1h,
                "recent_10m": recent_10m,
                "samples": samples,
            }
    finally:
        conn.close()


def get_price_data_status():
    """Get source price data status"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as price_records_1h,
                    COUNT(DISTINCT symbol) as price_symbols,
                    MAX(timestamp_iso) as latest_price
                FROM price_data_real
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
            )
            result = cursor.fetchone()
            return result
    finally:
        conn.close()


def print_monitoring_report():
    """Print the monitoring report"""
    print(f"\n{'='*60}")
    print(f"ML FEATURES MATERIALIZATION MONITOR")
    print(f"Timestamp: {datetime.now()}")
    print(f"{'='*60}")

    try:
        ml_status = get_ml_features_status()
        price_status = get_price_data_status()

        # Overall Status
        print(f"\n1. MATERIALIZED TABLE OVERVIEW")
        print(f"{'-'*40}")
        if ml_status["overall"]:
            total, symbols, latest_data, latest_update = ml_status["overall"]
            print(f"Total Records: {total:,}")
            print(f"Unique Symbols: {symbols}")
            print(f"Latest Data: {latest_data}")
            print(f"Latest Update: {latest_update}")

        # Recent Activity
        print(f"\n2. RECENT PROCESSING ACTIVITY")
        print(f"{'-'*40}")

        if ml_status["recent_1h"]:
            updates_1h, symbols_1h = ml_status["recent_1h"]
            print(f"Updates (Last Hour): {updates_1h}")
            print(f"Symbols (Last Hour): {symbols_1h}")

            if updates_1h > 0:
                print("Hourly Status: [ACTIVE] Processing ongoing")
            else:
                print("Hourly Status: [QUIET] No recent processing")

        if ml_status["recent_10m"]:
            updates_10m, symbols_10m = ml_status["recent_10m"]
            print(f"Updates (Last 10min): {updates_10m}")
            print(f"Symbols (Last 10min): {symbols_10m}")

            if updates_10m > 0:
                print("Current Status: [VERY ACTIVE] Real-time processing")
            else:
                print("Current Status: [IDLE] Waiting for new data")

        # Source Data Check
        print(f"\n3. SOURCE PRICE DATA STATUS")
        print(f"{'-'*40}")
        if price_status:
            price_records, price_symbols, latest_price = price_status
            print(f"Price Records (1h): {price_records}")
            print(f"Price Symbols: {price_symbols}")
            print(f"Latest Price: {latest_price}")

            if price_records > 0:
                print("Price Collection: [FLOWING] Fresh data available")
            else:
                print("Price Collection: [STOPPED] No recent price data")

        # Recent Processing Samples
        print(f"\n4. RECENT PROCESSING SAMPLES")
        print(f"{'-'*40}")
        if ml_status["samples"]:
            print(f"{'Symbol':<8} {'Data Time':<20} {'Update Time':<20}")
            print(f"{'-'*50}")
            for symbol, data_time, update_time in ml_status["samples"]:
                print(f"{symbol:<8} {str(data_time):<20} {str(update_time):<20}")
        else:
            print("No recent processing samples")

        # Health Assessment
        print(f"\n5. SYSTEM HEALTH ASSESSMENT")
        print(f"{'-'*40}")

        health_score = 0
        issues = []

        # Check recent ML updates
        if ml_status["recent_10m"] and ml_status["recent_10m"][0] > 0:
            print("[OK] ML features being updated in real-time")
            health_score += 40
        elif ml_status["recent_1h"] and ml_status["recent_1h"][0] > 0:
            print("[SLOW] ML features updating but slowly")
            health_score += 20
            issues.append("Slow ML processing")
        else:
            print("[PROBLEM] No recent ML feature updates")
            issues.append("ML processing stopped")

        # Check price data source
        if price_status and price_status[0] > 0:
            print("[OK] Source price data is flowing")
            health_score += 30
        else:
            print("[PROBLEM] No source price data")
            issues.append("Price data collection stopped")

        # Check symbol coverage
        if ml_status["overall"] and ml_status["overall"][1] > 100:
            print(f"[OK] Good symbol coverage ({ml_status['overall'][1]} symbols)")
            health_score += 30
        else:
            print("[WARNING] Limited symbol coverage")
            issues.append("Low symbol coverage")

        # Overall status
        print(f"\nOVERALL HEALTH SCORE: {health_score}/100")

        if health_score >= 80:
            print("SYSTEM STATUS: [EXCELLENT] All systems operating optimally")
        elif health_score >= 60:
            print("SYSTEM STATUS: [GOOD] Minor issues detected")
        elif health_score >= 40:
            print("SYSTEM STATUS: [FAIR] Some problems need attention")
        else:
            print("SYSTEM STATUS: [POOR] Significant issues require action")

        if issues:
            print(f"\nISSUES DETECTED:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

        return health_score >= 60

    except Exception as e:
        print(f"ERROR: Failed to generate report: {e}")
        return False


def continuous_monitoring(interval_minutes=5, total_checks=12):
    """Run continuous monitoring"""
    print(f"STARTING CONTINUOUS ML FEATURES MONITORING")
    print(f"Check interval: {interval_minutes} minutes")
    print(f"Total duration: {total_checks * interval_minutes} minutes")
    print(f"Press Ctrl+C to stop monitoring early")

    check_number = 0

    try:
        while check_number < total_checks:
            check_number += 1
            print(f"\n{'#'*60}")
            print(f"MONITORING CHECK {check_number}/{total_checks}")

            is_healthy = print_monitoring_report()

            if check_number < total_checks:
                print(f"\nNext check in {interval_minutes} minutes...")
                print(f"{'#'*60}")
                time.sleep(interval_minutes * 60)
            else:
                print(f"\nMONITORING COMPLETED after {total_checks} checks")

        print(f"\nFINAL STATUS: Monitoring session completed successfully")

    except KeyboardInterrupt:
        print(f"\n\nMONITORING STOPPED by user after {check_number} checks")
        print(f"Last check was healthy: {check_number > 0}")


def main():
    """Main execution with command line options"""
    print("ML Features Materialization Monitor")
    print("===================================")

    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            # Continuous monitoring mode
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            checks = int(sys.argv[3]) if len(sys.argv) > 3 else 12
            continuous_monitoring(interval, checks)
        elif sys.argv[1] == "help":
            print("Usage:")
            print("  python monitor_ml_features.py                    # Single check")
            print(
                "  python monitor_ml_features.py continuous         # Monitor for 1 hour (5min intervals)"
            )
            print(
                "  python monitor_ml_features.py continuous 3 20    # Monitor for 1 hour (3min intervals, 20 checks)"
            )
            print("  python monitor_ml_features.py help               # Show this help")
        else:
            print("Unknown option. Use 'help' for usage information.")
    else:
        # Single check mode (default)
        print_monitoring_report()


if __name__ == "__main__":
    main()

