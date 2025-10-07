#!/usr/bin/env python3
"""
Automated Data Collection Health Monitor
========================================

This script monitors the data collection system and alerts when:
1. ML feature processing stops or falls behind
2. Data collection gaps exceed thresholds
3. System health score drops below acceptable levels
4. Services become unavailable

Usage:
    python monitor_data_collection_health.py [--alert-threshold HOURS] [--check-interval MINUTES]
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import mysql.connector
import requests
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("data_collection_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class DataCollectionHealthMonitor:
    """Monitor data collection system health and alert on issues"""

    def __init__(
        self, alert_threshold_hours: int = 2, check_interval_minutes: int = 15
    ):
        self.alert_threshold_hours = alert_threshold_hours
        self.check_interval_minutes = check_interval_minutes
        self.db_config = {
            "host": "192.168.230.162",
            "user": "news_collector",
            "password": "99Rules!",
            "database": "crypto_prices",
            "charset": "utf8mb4",
        }
        self.alert_history = []

    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def check_ml_features_health(self) -> Dict[str, Any]:
        """Check ML features materialization health"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Get latest ML feature data
            cursor.execute(
                """
                SELECT 
                    MAX(timestamp_iso) as latest_data,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MAX(updated_at) as latest_update
                FROM ml_features_materialized
            """
            )
            ml_data = cursor.fetchone()

            # Get recent processing activity
            cursor.execute(
                """
                SELECT COUNT(*) as recent_updates
                FROM ml_features_materialized 
                WHERE updated_at >= %s
            """,
                (datetime.now() - timedelta(hours=1),),
            )
            recent_activity = cursor.fetchone()

            cursor.close()
            conn.close()

            # Calculate health metrics
            latest_data_time = ml_data["latest_data"]
            latest_update_time = ml_data["latest_update"]
            data_age_hours = (
                (datetime.now() - latest_data_time).total_seconds() / 3600
                if latest_data_time
                else 999
            )
            update_age_hours = (
                (datetime.now() - latest_update_time).total_seconds() / 3600
                if latest_update_time
                else 999
            )

            health_score = 100
            issues = []

            # Check data freshness
            if data_age_hours > self.alert_threshold_hours:
                health_score -= 40
                issues.append(
                    f"ML data is {data_age_hours:.1f} hours old (threshold: {self.alert_threshold_hours}h)"
                )

            # Check processing activity
            if recent_activity["recent_updates"] == 0:
                health_score -= 30
                issues.append("No ML feature updates in the last hour")

            # Check symbol coverage
            if ml_data["unique_symbols"] < 100:
                health_score -= 20
                issues.append(
                    f"Low symbol coverage: {ml_data['unique_symbols']} symbols"
                )

            return {
                "health_score": max(0, health_score),
                "latest_data": latest_data_time,
                "latest_update": latest_update_time,
                "data_age_hours": data_age_hours,
                "update_age_hours": update_age_hours,
                "total_records": ml_data["total_records"],
                "unique_symbols": ml_data["unique_symbols"],
                "recent_updates": recent_activity["recent_updates"],
                "issues": issues,
                "status": (
                    "healthy"
                    if health_score >= 80
                    else "warning" if health_score >= 60 else "critical"
                ),
            }

        except Exception as e:
            logger.error(f"Error checking ML features health: {e}")
            return {"health_score": 0, "status": "error", "error": str(e)}

    def check_price_data_health(self) -> Dict[str, Any]:
        """Check price data collection health"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Get latest price data
            cursor.execute(
                """
                SELECT 
                    MAX(timestamp_iso) as latest_price,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols
                FROM price_data_real
                WHERE timestamp_iso >= %s
            """,
                (datetime.now() - timedelta(hours=24),),
            )
            price_data = cursor.fetchone()

            cursor.close()
            conn.close()

            latest_price_time = price_data["latest_price"]
            price_age_hours = (
                (datetime.now() - latest_price_time).total_seconds() / 3600
                if latest_price_time
                else 999
            )

            health_score = 100
            issues = []

            # Check price data freshness
            if price_age_hours > 1:  # Price data should be very fresh
                health_score -= 50
                issues.append(f"Price data is {price_age_hours:.1f} hours old")

            # Check data volume
            if price_data["total_records"] < 1000:  # Should have many records in 24h
                health_score -= 30
                issues.append(
                    f"Low price data volume: {price_data['total_records']} records in 24h"
                )

            return {
                "health_score": max(0, health_score),
                "latest_price": latest_price_time,
                "price_age_hours": price_age_hours,
                "total_records": price_data["total_records"],
                "unique_symbols": price_data["unique_symbols"],
                "issues": issues,
                "status": (
                    "healthy"
                    if health_score >= 80
                    else "warning" if health_score >= 60 else "critical"
                ),
            }

        except Exception as e:
            logger.error(f"Error checking price data health: {e}")
            return {"health_score": 0, "status": "error", "error": str(e)}

    def check_kubernetes_services(self) -> Dict[str, Any]:
        """Check Kubernetes services health"""
        try:
            # This would typically use kubectl or Kubernetes API
            # For now, we'll check if we can connect to the API gateway
            try:
                response = requests.get(
                    "http://simple-api-gateway.crypto-collectors.svc.cluster.local:8000/health",
                    timeout=10,
                )
                if response.status_code == 200:
                    api_health = response.json()
                    return {
                        "health_score": (
                            100 if api_health.get("status") == "healthy" else 50
                        ),
                        "api_gateway_status": api_health.get("status", "unknown"),
                        "components": api_health.get("components", {}),
                        "status": (
                            "healthy"
                            if api_health.get("status") == "healthy"
                            else "warning"
                        ),
                    }
                else:
                    return {
                        "health_score": 0,
                        "api_gateway_status": "unhealthy",
                        "status": "critical",
                        "error": f"API Gateway returned status {response.status_code}",
                    }
            except requests.exceptions.RequestException as e:
                return {
                    "health_score": 0,
                    "api_gateway_status": "unreachable",
                    "status": "critical",
                    "error": str(e),
                }

        except Exception as e:
            logger.error(f"Error checking Kubernetes services: {e}")
            return {"health_score": 0, "status": "error", "error": str(e)}

    def calculate_overall_health(
        self, ml_health: Dict, price_health: Dict, k8s_health: Dict
    ) -> Dict[str, Any]:
        """Calculate overall system health"""
        scores = [
            ml_health["health_score"],
            price_health["health_score"],
            k8s_health["health_score"],
        ]
        overall_score = sum(scores) / len(scores)

        all_issues = []
        all_issues.extend(ml_health.get("issues", []))
        all_issues.extend(price_health.get("issues", []))
        if k8s_health.get("error"):
            all_issues.append(f"K8s Services: {k8s_health['error']}")

        status = "healthy"
        if overall_score < 60:
            status = "critical"
        elif overall_score < 80:
            status = "warning"

        return {
            "overall_score": overall_score,
            "status": status,
            "issues": all_issues,
            "ml_health": ml_health,
            "price_health": price_health,
            "k8s_health": k8s_health,
        }

    def send_alert(self, health_data: Dict[str, Any]):
        """Send alert for critical issues"""
        if health_data["status"] in ["critical", "warning"]:
            alert_message = f"""
🚨 DATA COLLECTION HEALTH ALERT 🚨

Status: {health_data['status'].upper()}
Overall Health Score: {health_data['overall_score']:.1f}/100
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Issues Detected:
{chr(10).join(f"• {issue}" for issue in health_data['issues'])}

ML Features Health: {health_data['ml_health']['health_score']}/100
Price Data Health: {health_data['price_health']['health_score']}/100
K8s Services Health: {health_data['k8s_health']['health_score']}/100

Action Required: Please investigate and resolve the issues above.
            """

            logger.warning(f"ALERT: {alert_message}")

            # Store alert in history
            self.alert_history.append(
                {
                    "timestamp": datetime.now(),
                    "status": health_data["status"],
                    "score": health_data["overall_score"],
                    "issues": health_data["issues"],
                }
            )

            # Keep only last 100 alerts
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]

    def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check"""
        logger.info("🔍 Running data collection health check...")

        # Check all components
        ml_health = self.check_ml_features_health()
        price_health = self.check_price_data_health()
        k8s_health = self.check_kubernetes_services()

        # Calculate overall health
        overall_health = self.calculate_overall_health(
            ml_health, price_health, k8s_health
        )

        # Log results
        logger.info(f"📊 Health Check Results:")
        logger.info(
            f"   Overall Score: {overall_health['overall_score']:.1f}/100 ({overall_health['status']})"
        )
        logger.info(f"   ML Features: {ml_health['health_score']}/100")
        logger.info(f"   Price Data: {price_health['health_score']}/100")
        logger.info(f"   K8s Services: {k8s_health['health_score']}/100")

        if overall_health["issues"]:
            logger.warning(f"⚠️ Issues detected: {len(overall_health['issues'])}")
            for issue in overall_health["issues"]:
                logger.warning(f"   • {issue}")

        # Send alert if needed
        self.send_alert(overall_health)

        return overall_health

    def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        logger.info(
            f"🚀 Starting continuous monitoring (check every {self.check_interval_minutes} minutes)"
        )
        logger.info(f"📊 Alert threshold: {self.alert_threshold_hours} hours")

        while True:
            try:
                health_data = self.run_health_check()

                # Log summary
                if health_data["status"] == "healthy":
                    logger.info("✅ All systems healthy")
                elif health_data["status"] == "warning":
                    logger.warning("⚠️ System warnings detected")
                else:
                    logger.error("🚨 Critical system issues detected")

                # Wait for next check
                logger.info(
                    f"⏰ Next check in {self.check_interval_minutes} minutes..."
                )
                time.sleep(self.check_interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    parser = argparse.ArgumentParser(description="Data Collection Health Monitor")
    parser.add_argument(
        "--alert-threshold",
        type=int,
        default=2,
        help="Alert threshold in hours for data age (default: 2)",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=15,
        help="Check interval in minutes (default: 15)",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run health check once and exit"
    )

    args = parser.parse_args()

    monitor = DataCollectionHealthMonitor(
        alert_threshold_hours=args.alert_threshold,
        check_interval_minutes=args.check_interval,
    )

    if args.once:
        health_data = monitor.run_health_check()
        print(json.dumps(health_data, indent=2, default=str))
    else:
        monitor.run_continuous_monitoring()


if __name__ == "__main__":
    main()
