#!/usr/bin/env python3

import mysql.connector
import logging
import time
import json
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection(database='crypto_prices'):
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database=database
    )


def monitor_collection_health():
    """Monitor the health of all collection services"""
    try:
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        print(f"\n🔍 COLLECTION HEALTH MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Check recent data collection activity
        checks = [
            {
                'name': 'Price Data Collection',
                'table': 'crypto_prices.ml_features_materialized',
                'time_column': 'created_at',
                'max_age_hours': 2,
                'critical_age_hours': 6
            },
            {
                'name': 'OHLC Data Collection', 
                'table': 'crypto_prices.ohlc_data',
                'time_column': 'timestamp',
                'max_age_hours': 24,
                'critical_age_hours': 48
            }
        ]
        
        # Check crypto_news database
        news_conn = get_db_connection('crypto_news')
        news_cursor = news_conn.cursor()
        
        news_checks = [
            {
                'name': 'News Collection',
                'table': 'crypto_news_data',
                'time_column': 'created_at',
                'max_age_hours': 12,
                'critical_age_hours': 24
            },
            {
                'name': 'Social Media Collection',
                'table': 'social_media_posts',
                'time_column': 'created_at',
                'max_age_hours': 24,
                'critical_age_hours': 48
            },
            {
                'name': 'Sentiment Processing',
                'table': 'sentiment_data',
                'time_column': 'created_at',
                'max_age_hours': 24,
                'critical_age_hours': 48
            }
        ]
        
        health_status = {}
        
        # Check crypto_prices collections
        for check in checks:
            cursor.execute(f"""
                SELECT 
                    MAX({check['time_column']}) as latest,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN {check['time_column']} >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                    COUNT(CASE WHEN {check['time_column']} >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
                FROM {check['table']}
            """)
            
            result = cursor.fetchone()
            latest = result[0]
            total = result[1]
            recent_1h = result[2]
            recent_24h = result[3]
            
            if latest:
                age_hours = (datetime.now() - latest).total_seconds() / 3600
                
                if age_hours <= check['max_age_hours']:
                    status = "✅ HEALTHY"
                elif age_hours <= check['critical_age_hours']:
                    status = "⚠️ WARNING"
                else:
                    status = "🚨 CRITICAL"
                    
                health_status[check['name']] = {
                    'status': status,
                    'latest': latest,
                    'age_hours': age_hours,
                    'recent_1h': recent_1h,
                    'recent_24h': recent_24h,
                    'total': total
                }
                
                print(f"{status} {check['name']}")
                print(f"   Latest: {latest} ({age_hours:.1f}h ago)")
                print(f"   Recent: {recent_1h} (1h), {recent_24h} (24h), {total:,} total")
            else:
                health_status[check['name']] = {
                    'status': "❌ NO DATA",
                    'latest': None,
                    'age_hours': float('inf'),
                    'recent_1h': 0,
                    'recent_24h': 0,
                    'total': total
                }
                print(f"❌ NO DATA {check['name']} - {total:,} total records")
        
        # Check crypto_news collections
        for check in news_checks:
            news_cursor.execute(f"""
                SELECT 
                    MAX({check['time_column']}) as latest,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN {check['time_column']} >= DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 1 END) as recent_1h,
                    COUNT(CASE WHEN {check['time_column']} >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as recent_24h
                FROM {check['table']}
            """)
            
            result = news_cursor.fetchone()
            latest = result[0]
            total = result[1]
            recent_1h = result[2]
            recent_24h = result[3]
            
            if latest:
                age_hours = (datetime.now() - latest).total_seconds() / 3600
                
                if age_hours <= check['max_age_hours']:
                    status = "✅ HEALTHY"
                elif age_hours <= check['critical_age_hours']:
                    status = "⚠️ WARNING"
                else:
                    status = "🚨 CRITICAL"
                    
                health_status[check['name']] = {
                    'status': status,
                    'latest': latest,
                    'age_hours': age_hours,
                    'recent_1h': recent_1h,
                    'recent_24h': recent_24h,
                    'total': total
                }
                
                print(f"{status} {check['name']}")
                print(f"   Latest: {latest} ({age_hours:.1f}h ago)")
                print(f"   Recent: {recent_1h} (1h), {recent_24h} (24h), {total:,} total")
            else:
                health_status[check['name']] = {
                    'status': "❌ NO DATA",
                    'latest': None,
                    'age_hours': float('inf'),
                    'recent_1h': 0,
                    'recent_24h': 0,
                    'total': total
                }
                print(f"❌ NO DATA {check['name']} - {total:,} total records")
        
        cursor.close()
        news_cursor.close()
        conn.close()
        news_conn.close()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error monitoring collection health: {e}")
        return {}


def monitor_sentiment_integration():
    """Monitor sentiment data integration into ML features"""
    try:
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        print(f"\n🧠 SENTIMENT INTEGRATION MONITORING")
        print("=" * 80)
        
        # Check sentiment coverage in ML features
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_cryptobert,
                SUM(CASE WHEN avg_vader_score IS NOT NULL THEN 1 ELSE 0 END) as has_vader,
                SUM(CASE WHEN avg_textblob_score IS NOT NULL THEN 1 ELSE 0 END) as has_textblob,
                SUM(CASE WHEN avg_finbert_sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as has_finbert,
                SUM(CASE WHEN social_avg_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_social,
                SUM(CASE WHEN news_sentiment IS NOT NULL THEN 1 ELSE 0 END) as has_news,
                SUM(CASE WHEN crypto_sentiment_count > 0 THEN 1 ELSE 0 END) as has_count
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        sentiment_status = {}
        
        if total > 0:
            sentiment_types = [
                ('CryptoBERT', result[1]),
                ('VADER', result[2]),
                ('TextBlob', result[3]),
                ('FinBERT', result[4]),
                ('Social', result[5]),
                ('News', result[6]),
                ('Count', result[7])
            ]
            
            print(f"📊 Sentiment Coverage (Last 24h, {total:,} records):")
            
            for name, count in sentiment_types:
                percentage = (count / total * 100) if total > 0 else 0
                
                if percentage >= 10:
                    status = "✅ GOOD"
                elif percentage >= 2:
                    status = "⚠️ LOW"
                elif percentage > 0:
                    status = "🔸 MINIMAL"
                else:
                    status = "❌ NONE"
                
                sentiment_status[name] = {
                    'count': count,
                    'percentage': percentage,
                    'status': status
                }
                
                print(f"  {status} {name}: {count:,} ({percentage:.1f}%)")
        
        # Check recent sentiment processing activity
        cursor.execute("""
            SELECT 
                COUNT(*) as updated_1h,
                COUNT(CASE WHEN avg_cryptobert_score IS NOT NULL 
                           OR social_avg_sentiment IS NOT NULL 
                           OR news_sentiment IS NOT NULL THEN 1 END) as sentiment_updates_1h
            FROM ml_features_materialized
            WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        
        result = cursor.fetchone()
        updated_1h = result[0]
        sentiment_updates_1h = result[1]
        
        print(f"\n⏰ Recent Activity (Last 1 hour):")
        print(f"  Total updates: {updated_1h:,}")
        print(f"  Sentiment updates: {sentiment_updates_1h:,}")
        
        # Check top symbols with sentiment
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as records,
                AVG(avg_cryptobert_score) as avg_cb,
                AVG(social_avg_sentiment) as avg_social,
                AVG(news_sentiment) as avg_news
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
              AND (avg_cryptobert_score IS NOT NULL 
                   OR social_avg_sentiment IS NOT NULL 
                   OR news_sentiment IS NOT NULL)
            GROUP BY symbol
            ORDER BY records DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"\n🏆 Top symbols with sentiment (24h):")
            print(f"{'Symbol':<8} {'Records':<8} {'CryptoBERT':<10} {'Social':<8} {'News':<8}")
            print("-" * 50)
            for row in results:
                symbol = row[0]
                records = row[1]
                cb_score = row[2] if row[2] else 0
                social_score = row[3] if row[3] else 0
                news_score = row[4] if row[4] else 0
                print(f"{symbol:<8} {records:<8} {cb_score:<10.3f} {social_score:<8.3f} {news_score:<8.3f}")
        
        cursor.close()
        conn.close()
        
        sentiment_status['recent_updates'] = {
            'total_updates_1h': updated_1h,
            'sentiment_updates_1h': sentiment_updates_1h,
            'top_symbols_count': len(results)
        }
        
        return sentiment_status
        
    except Exception as e:
        logger.error(f"Error monitoring sentiment integration: {e}")
        return {}


def update_monitoring_alerts(health_status, sentiment_status):
    """Update monitoring alerts based on current status"""
    try:
        conn = get_db_connection('crypto_prices')
        cursor = conn.cursor()
        
        print(f"\n📢 UPDATING MONITORING ALERTS")
        print("=" * 80)
        
        alerts_created = 0
        
        # Check collection health alerts
        for service_name, status_info in health_status.items():
            if status_info['status'].startswith('🚨'):
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('critical_data_age', %s, 'critical')
                    ON DUPLICATE KEY UPDATE 
                        created_at = NOW(),
                        resolved = FALSE
                """, (f"{service_name} data is {status_info['age_hours']:.1f}h old",))
                alerts_created += 1
                
            elif status_info['status'].startswith('⚠️'):
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('warning_data_age', %s, 'warning')
                    ON DUPLICATE KEY UPDATE 
                        created_at = NOW(),
                        resolved = FALSE
                """, (f"{service_name} data is {status_info['age_hours']:.1f}h old",))
                alerts_created += 1
        
        # Check sentiment integration alerts
        for sentiment_type, status_info in sentiment_status.items():
            if sentiment_type != 'recent_updates' and status_info['percentage'] < 1:
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('low_sentiment_coverage', %s, 'warning')
                    ON DUPLICATE KEY UPDATE 
                        created_at = NOW(),
                        resolved = FALSE
                """, (f"{sentiment_type} sentiment coverage is {status_info['percentage']:.1f}%",))
                alerts_created += 1
        
        # Check recent activity
        if 'recent_updates' in sentiment_status:
            recent = sentiment_status['recent_updates']
            if recent['sentiment_updates_1h'] == 0:
                cursor.execute("""
                    INSERT INTO monitoring_alerts (alert_type, message, severity)
                    VALUES ('no_recent_sentiment', 'No sentiment updates in last hour', 'warning')
                    ON DUPLICATE KEY UPDATE 
                        created_at = NOW(),
                        resolved = FALSE
                """)
                alerts_created += 1
        
        # Update service monitoring status
        for service_name, status_info in health_status.items():
            service_key = service_name.lower().replace(' ', '_')
            cursor.execute("""
                UPDATE collection_monitoring 
                SET 
                    status = %s,
                    last_collection = %s,
                    records_collected = %s,
                    updated_at = NOW()
                WHERE service_name LIKE %s
            """, (
                status_info['status'],
                status_info['latest'],
                status_info['recent_24h'],
                f"%{service_key}%"
            ))
        
        conn.commit()
        
        print(f"✅ Created/updated {alerts_created} monitoring alerts")
        
        # Show current active alerts
        cursor.execute("""
            SELECT alert_type, message, severity, created_at
            FROM monitoring_alerts
            WHERE resolved = FALSE
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1 
                    WHEN 'error' THEN 2 
                    WHEN 'warning' THEN 3 
                    ELSE 4 
                END,
                created_at DESC
            LIMIT 10
        """)
        
        alerts = cursor.fetchall()
        if alerts:
            print(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
            for alert_type, message, severity, created_at in alerts:
                severity_emoji = {
                    'critical': '🚨',
                    'error': '❌', 
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(severity, '📢')
                print(f"  {severity_emoji} {severity.upper()}: {message} ({created_at})")
        else:
            print("✅ No active alerts")
        
        cursor.close()
        conn.close()
        
        return alerts_created
        
    except Exception as e:
        logger.error(f"Error updating monitoring alerts: {e}")
        return 0


def generate_monitoring_summary(health_status, sentiment_status):
    """Generate overall monitoring summary"""
    try:
        print(f"\n📊 MONITORING SUMMARY")
        print("=" * 80)
        
        # Overall health score
        total_services = len(health_status)
        healthy_services = sum(1 for status in health_status.values() if status['status'].startswith('✅'))
        warning_services = sum(1 for status in health_status.values() if status['status'].startswith('⚠️'))
        critical_services = sum(1 for status in health_status.values() if status['status'].startswith('🚨'))
        
        health_score = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        print(f"🏥 Collection Health Score: {health_score:.1f}%")
        print(f"   ✅ Healthy: {healthy_services}/{total_services}")
        print(f"   ⚠️ Warning: {warning_services}/{total_services}")
        print(f"   🚨 Critical: {critical_services}/{total_services}")
        
        # Sentiment integration score
        if sentiment_status and 'recent_updates' in sentiment_status:
            sentiment_types = [k for k in sentiment_status.keys() if k != 'recent_updates']
            active_sentiment = sum(1 for k in sentiment_types if sentiment_status[k]['percentage'] > 0)
            sentiment_score = (active_sentiment / len(sentiment_types) * 100) if sentiment_types else 0
            
            recent = sentiment_status['recent_updates']
            
            print(f"\n🧠 Sentiment Integration Score: {sentiment_score:.1f}%")
            print(f"   Active types: {active_sentiment}/{len(sentiment_types)}")
            print(f"   Recent updates: {recent['sentiment_updates_1h']} (1h)")
            print(f"   Top symbols: {recent['top_symbols_count']}")
        
        # Overall system status
        if health_score >= 80 and sentiment_score >= 20:
            overall_status = "🎉 EXCELLENT"
        elif health_score >= 60 and sentiment_score >= 10:
            overall_status = "✅ GOOD"
        elif health_score >= 40:
            overall_status = "⚠️ NEEDS ATTENTION"
        else:
            overall_status = "🚨 CRITICAL ISSUES"
        
        print(f"\n🎯 Overall System Status: {overall_status}")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"📅 Last checked: {timestamp}")
        
        return {
            'health_score': health_score,
            'sentiment_score': sentiment_score,
            'overall_status': overall_status,
            'timestamp': timestamp
        }
        
    except Exception as e:
        logger.error(f"Error generating monitoring summary: {e}")
        return {}


def main_monitoring_cycle():
    """Main monitoring cycle"""
    logger.info("Starting comprehensive monitoring cycle...")
    
    try:
        # Monitor collection health
        health_status = monitor_collection_health()
        
        # Monitor sentiment integration
        sentiment_status = monitor_sentiment_integration()
        
        # Update alerts
        alerts_created = update_monitoring_alerts(health_status, sentiment_status)
        
        # Generate summary
        summary = generate_monitoring_summary(health_status, sentiment_status)
        
        print(f"\n" + "=" * 80)
        print(f"🔄 MONITORING CYCLE COMPLETED")
        print(f"   Health checks: {len(health_status)} services")
        print(f"   Sentiment checks: {len(sentiment_status)} types")
        print(f"   Alerts created: {alerts_created}")
        print(f"   Overall status: {summary.get('overall_status', 'Unknown')}")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in monitoring cycle: {e}")
        return False


def continuous_monitoring(check_interval=300):  # 5 minutes
    """Run continuous monitoring"""
    logger.info(f"Starting continuous monitoring (check every {check_interval}s)...")
    
    print("🔄 CONTINUOUS MONITORING STARTED")
    print(f"Check interval: {check_interval} seconds ({check_interval/60:.1f} minutes)")
    print("=" * 80)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n🔄 MONITORING CYCLE #{cycle_count}")
            
            success = main_monitoring_cycle()
            
            if not success:
                logger.warning(f"Monitoring cycle #{cycle_count} failed")
            
            print(f"\n⏰ Next check in {check_interval/60:.1f} minutes...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        logger.info(f"Continuous monitoring stopped after {cycle_count} cycles")
    except Exception as e:
        logger.error(f"Critical error in continuous monitoring: {e}")


if __name__ == "__main__":
    # Run one monitoring cycle first
    print("🚀 STARTING ONGOING MONITORING SYSTEM")
    print("=" * 80)
    
    # Single cycle for immediate check
    main_monitoring_cycle()
    
    # Ask if user wants continuous monitoring
    print(f"\n" + "=" * 80)
    print("MONITORING OPTIONS:")
    print("1. Single check completed above")
    print("2. For continuous monitoring, run with:")
    print("   python ongoing_monitoring.py --continuous")
    print("3. Or call continuous_monitoring() function directly")
    print("=" * 80)