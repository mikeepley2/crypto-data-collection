#!/usr/bin/env python3
"""
Quick Collection Status Check
Shows current status of all collectors without continuous monitoring
"""

import subprocess
import mysql.connector
from datetime import datetime
from typing import Dict


def get_db_connection(database: str):
    """Get database connection"""
    config = {
        'host': 'host.docker.internal',
        'user': 'news_collector', 
        'password': '99Rules!',
        'database': database,
        'charset': 'utf8mb4'
    }
    return mysql.connector.connect(**config)


def get_collector_manager_pod():
    """Get collector manager pod name"""
    try:
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '-l', 'app=collector-manager', '--field-selector=status.phase=Running',
            '-o', 'jsonpath={.items[0].metadata.name}'
        ], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None


def check_recent_data():
    """Check recent data collection across all services"""
    
    services = {
        'enhanced-crypto-prices': {'database': 'crypto_prices', 'table': 'crypto_prices', 'time_col': 'timestamp'},
        'crypto-news-collector': {'database': 'crypto_news', 'table': 'crypto_news', 'time_col': 'published_date'},
        'stock-news-collector': {'database': 'crypto_news', 'table': 'stock_news', 'time_col': 'published_date'},
        'technical-indicators': {'database': 'crypto_prices', 'table': 'technical_indicators', 'time_col': 'timestamp'},
        'macro-economic': {'database': 'crypto_prices', 'table': 'macro_indicators', 'time_col': 'timestamp'},
        'social-other': {'database': 'crypto_news', 'table': 'reddit_posts', 'time_col': 'created_at'},
        'onchain-data-collector': {'database': 'crypto_prices', 'table': 'onchain_metrics', 'time_col': 'timestamp'},
    }
    
    results = {}
    
    for service_name, config in services.items():
        try:
            query = f"""
                SELECT 
                    COUNT(*) as count_1h,
                    (SELECT COUNT(*) FROM {config['table']} 
                     WHERE {config['time_col']} >= DATE_SUB(NOW(), INTERVAL 24 HOUR)) as count_24h,
                    MAX({config['time_col']}) as latest
                FROM {config['table']} 
                WHERE {config['time_col']} >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
            
            with get_db_connection(config['database']) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query)
                result = cursor.fetchone()
                results[service_name] = result
                
        except Exception as e:
            results[service_name] = {'count_1h': 0, 'count_24h': 0, 'latest': None, 'error': str(e)}
    
    return results


def check_pod_health():
    """Check pod health status"""
    try:
        result = subprocess.run([
            'kubectl', 'get', 'pods', '-n', 'crypto-collectors',
            '--no-headers'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            return {}
            
        pod_status = {}
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                ready = parts[1]
                status = parts[2]
                
                # Extract service name from pod name
                for service in ['enhanced-crypto-prices', 'crypto-news-collector', 'stock-news-collector', 
                              'technical-indicators', 'macro-economic', 'social-other', 
                              'onchain-data-collector', 'collector-manager']:
                    if service in name:
                        pod_status[service] = {'ready': ready, 'status': status}
                        break
        
        return pod_status
        
    except Exception as e:
        print(f"Error checking pod health: {e}")
        return {}


def main():
    """Main status check"""
    print("CRYPTO COLLECTION SYSTEM - QUICK STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check pod health
    print("\nPOD STATUS:")
    print("-" * 40)
    pod_status = check_pod_health()
    
    services = ['collector-manager', 'enhanced-crypto-prices', 'crypto-news-collector', 
               'stock-news-collector', 'technical-indicators', 'macro-economic', 
               'social-other', 'onchain-data-collector']
    
    for service in services:
        if service in pod_status:
            status = pod_status[service]
            health = "OK" if status['status'] == 'Running' and '1/1' in status['ready'] else "ISSUE"
            print(f"{service:<25} | {health:<5} | {status['status']}")
        else:
            print(f"{service:<25} | MISS  | Not Found")
    
    # Check data collection
    print("\nDATA COLLECTION STATUS:")
    print("-" * 60)
    print("SERVICE                  | 1H COUNT | 24H COUNT | LATEST")
    print("-" * 60)
    
    data_status = check_recent_data()
    
    for service_name, data in data_status.items():
        if 'error' in data:
            print(f"{service_name:<24} | ERROR    | ERROR     | {data['error'][:20]}")
        else:
            latest = str(data['latest'])[:19] if data['latest'] else "Never"
            count_1h = data.get('count_1h', 0)
            count_24h = data.get('count_24h', 0)
            
            # Status indicator
            status = "OK" if count_1h > 0 else "LOW" if count_24h > 0 else "NONE"
            
            print(f"{service_name:<24} | {status} {count_1h:<5} | {count_24h:<8} | {latest}")
    
    print("-" * 60)
    
    # Check collector manager
    manager_pod = get_collector_manager_pod()
    if manager_pod:
        print(f"\nCollector Manager: {manager_pod} (Running)")
    else:
        print("\nCollector Manager: NOT FOUND")
    
    print("\nTo start continuous monitoring, run:")
    print("python simple_collection_monitor.py")


if __name__ == "__main__":
    main()