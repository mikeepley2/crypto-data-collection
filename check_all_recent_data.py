#!/usr/bin/env python3
"""
Comprehensive Recent Data Check
Verify all identified enhanced tables have recent data flowing
"""

import mysql.connector
from datetime import datetime, timedelta

def check_all_tables_recent_data():
    """Check recent data in all identified key tables"""
    
    print("🔍 COMPREHENSIVE RECENT DATA CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Checking for data in last 1 hour, 6 hours, and 24 hours")
    print("=" * 60)
    
    # Database connection
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '99Rules!',
        'charset': 'utf8mb4'
    }
    
    # Define all our key tables with their timestamp columns
    key_tables = {
        'crypto_prices': {
            'ml_features_materialized': {
                'timestamp_col': 'timestamp_iso',
                'description': 'Primary ML features table (3.3M records, 117 columns)',
                'priority': 'CRITICAL'
            },
            'price_data_real': {
                'timestamp_col': 'timestamp_iso',
                'description': 'Comprehensive price data (3.8M records, 49 columns)',
                'priority': 'HIGH'
            },
            'crypto_onchain_data': {
                'timestamp_col': 'timestamp',
                'description': 'Onchain metrics data',
                'priority': 'CRITICAL'
            },
            'technical_indicators': {
                'timestamp_col': 'timestamp',
                'description': 'Technical analysis indicators',
                'priority': 'MEDIUM'
            }
        },
        'crypto_news': {
            'crypto_news_data': {
                'timestamp_col': 'timestamp',
                'description': 'Crypto-specific news articles',
                'priority': 'CRITICAL'
            },
            'news_data': {
                'timestamp_col': 'published_at',
                'description': 'General news data (275K records)',
                'priority': 'HIGH'
            },
            'crypto_sentiment_data': {
                'timestamp_col': 'timestamp',
                'description': 'Crypto sentiment analysis',
                'priority': 'HIGH'
            },
            'social_media_posts': {
                'timestamp_col': 'timestamp',
                'description': 'Social media content',
                'priority': 'MEDIUM'
            },
            'social_sentiment_data': {
                'timestamp_col': 'timestamp',
                'description': 'Social sentiment analysis',
                'priority': 'MEDIUM'
            }
        }
    }
    
    overall_results = {
        'active_tables': [],
        'inactive_tables': [],
        'error_tables': []
    }
    
    for db_name, tables in key_tables.items():
        print(f"\n📊 DATABASE: {db_name.upper()}")
        print("-" * 50)
        
        try:
            config = db_config.copy()
            config['database'] = db_name
            
            with mysql.connector.connect(**config) as conn:
                cursor = conn.cursor()
                
                for table_name, info in tables.items():
                    try:
                        # Get total count
                        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                        total_count = cursor.fetchone()[0]
                        
                        # Check recent data at different intervals
                        intervals = [
                            ('1 HOUR', 1),
                            ('6 HOUR', 6), 
                            ('24 HOUR', 24)
                        ]
                        
                        recent_data = {}
                        latest_timestamp = None
                        
                        for interval_name, hours in intervals:
                            cursor.execute(f"""
                                SELECT COUNT(*) as recent_count, MAX(`{info['timestamp_col']}`) as latest 
                                FROM `{table_name}` 
                                WHERE `{info['timestamp_col']}` >= DATE_SUB(NOW(), INTERVAL {hours} HOUR)
                            """)
                            
                            result = cursor.fetchone()
                            recent_data[interval_name] = result[0] if result else 0
                            if latest_timestamp is None and result:
                                latest_timestamp = result[1]
                        
                        # Determine status
                        status_icon = "🟢" if recent_data['1 HOUR'] > 0 else "🟡" if recent_data['6 HOUR'] > 0 else "🔴" if recent_data['24 HOUR'] > 0 else "❌"
                        
                        priority_icon = "⭐" if info['priority'] == 'CRITICAL' else "🔸" if info['priority'] == 'HIGH' else "◽"
                        
                        print(f"  {status_icon}{priority_icon} {table_name}")
                        print(f"     Total: {total_count:,} records")
                        print(f"     Recent: 1h:{recent_data['1 HOUR']:>4} | 6h:{recent_data['6 HOUR']:>4} | 24h:{recent_data['24 HOUR']:>4}")
                        print(f"     Latest: {latest_timestamp}")
                        print(f"     {info['description']}")
                        print()
                        
                        # Categorize results
                        table_info = {
                            'database': db_name,
                            'table': table_name,
                            'total': total_count,
                            'recent_1h': recent_data['1 HOUR'],
                            'recent_6h': recent_data['6 HOUR'],
                            'recent_24h': recent_data['24 HOUR'],
                            'latest': latest_timestamp,
                            'priority': info['priority']
                        }
                        
                        if recent_data['1 HOUR'] > 0:
                            overall_results['active_tables'].append(table_info)
                        elif recent_data['24 HOUR'] > 0:
                            overall_results['inactive_tables'].append(table_info)
                        else:
                            overall_results['inactive_tables'].append(table_info)
                            
                    except Exception as e:
                        print(f"  ❌ {table_name}: ERROR - {e}")
                        overall_results['error_tables'].append({
                            'database': db_name,
                            'table': table_name,
                            'error': str(e),
                            'priority': info['priority']
                        })
                        
        except Exception as e:
            print(f"❌ Database connection error for {db_name}: {e}")
    
    # Summary Report
    print(f"\n📋 SUMMARY REPORT")
    print("=" * 40)
    
    print(f"\n🟢 ACTIVE TABLES (Recent data in last hour):")
    print("-" * 45)
    if overall_results['active_tables']:
        for table in overall_results['active_tables']:
            priority_icon = "⭐" if table['priority'] == 'CRITICAL' else "🔸" if table['priority'] == 'HIGH' else "◽"
            print(f"  {priority_icon} {table['database']}.{table['table']:25} | {table['recent_1h']:>4} records | {table['priority']}")
    else:
        print("  ⚠️  No tables with data in last hour!")
    
    print(f"\n🟡 INACTIVE TABLES (No recent data in last hour):")
    print("-" * 50)
    if overall_results['inactive_tables']:
        for table in overall_results['inactive_tables']:
            priority_icon = "⭐" if table['priority'] == 'CRITICAL' else "🔸" if table['priority'] == 'HIGH' else "◽"
            status = f"24h:{table['recent_24h']}" if table['recent_24h'] > 0 else "NO RECENT DATA"
            print(f"  {priority_icon} {table['database']}.{table['table']:25} | {status} | {table['priority']}")
    else:
        print("  ✅ All tables have recent data!")
    
    if overall_results['error_tables']:
        print(f"\n❌ ERROR TABLES:")
        print("-" * 20)
        for table in overall_results['error_tables']:
            priority_icon = "⭐" if table['priority'] == 'CRITICAL' else "🔸" if table['priority'] == 'HIGH' else "◽"
            print(f"  {priority_icon} {table['database']}.{table['table']:25} | {table['error']}")
    
    # Health Score
    total_critical = len([t for t in key_tables['crypto_prices'].values() if t['priority'] == 'CRITICAL']) + \
                    len([t for t in key_tables['crypto_news'].values() if t['priority'] == 'CRITICAL'])
    
    active_critical = len([t for t in overall_results['active_tables'] if t['priority'] == 'CRITICAL'])
    
    health_score = (active_critical / total_critical * 100) if total_critical > 0 else 0
    
    print(f"\n🎯 SYSTEM HEALTH SCORE")
    print("-" * 25)
    print(f"Critical tables active: {active_critical}/{total_critical}")
    print(f"Health score: {health_score:.1f}%")
    
    if health_score >= 80:
        print("✅ EXCELLENT - System is collecting data actively")
    elif health_score >= 60:
        print("🟡 GOOD - Most critical systems working")
    elif health_score >= 40:
        print("⚠️  FAIR - Some critical systems need attention")
    else:
        print("❌ POOR - Critical systems not collecting data")
    
    print(f"\n🔍 LEGEND:")
    print("🟢 = Active (data in last hour)")
    print("🟡 = Recent (data in last 6-24 hours)")
    print("🔴 = Stale (no data in 24+ hours)")
    print("⭐ = Critical system")
    print("🔸 = High priority")
    print("◽ = Medium priority")
    
    return overall_results

if __name__ == "__main__":
    results = check_all_tables_recent_data()
    
    print(f"\n✨ Recent data check completed!")
    print(f"🎯 Review results above to confirm system health")