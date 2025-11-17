#!/usr/bin/env python3
"""
Quick Collector Table Assessment
===============================
Fast analysis of collector tables to identify immediate issues
"""

import mysql.connector
import os
from datetime import datetime, date
import json

class QuickTableAssessment:
    def __init__(self):
        self.db_config = {
            'host': '172.22.32.1',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices',
            'port': 3306,
            'autocommit': True,
            'charset': 'utf8mb4'
        }
        
        self.key_tables = {
            'price_data_real': {
                'expected_columns': ['symbol', 'timestamp', 'price_usd', 'volume_24h', 'market_cap'],
                'collector': 'enhanced_crypto_prices_service.py'
            },
            'technical_indicators': {
                'expected_columns': ['symbol', 'timestamp', 'sma_20', 'ema_20', 'rsi'],
                'collector': 'enhanced_crypto_prices_service.py'
            },
            'crypto_onchain_data': {
                'expected_columns': ['coin_symbol', 'timestamp', 'active_addresses', 'transaction_count'],
                'collector': 'onchain_collector_free.py'
            },
            'ohlc_data': {
                'expected_columns': ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'],
                'collector': 'enhanced_crypto_prices_service.py'
            }
        }

    def get_connection(self):
        return mysql.connector.connect(**self.db_config)

    def check_table_status(self, table_name, table_info):
        """Quick check of table status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if table exists and get basic info
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            exists = cursor.fetchone() is not None
            
            if not exists:
                cursor.close()
                conn.close()
                return {'status': 'missing', 'table': table_name}
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
            
            # Get column info
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row['Field'] for row in cursor.fetchall()]
            
            # Check for expected columns
            expected = set(table_info['expected_columns'])
            actual = set(columns)
            missing_columns = expected - actual
            
            # Get date range
            if 'timestamp' in columns:
                cursor.execute(f"""
                    SELECT 
                        MIN(timestamp) as earliest,
                        MAX(timestamp) as latest,
                        COUNT(DISTINCT DATE(timestamp)) as unique_dates
                    FROM {table_name} 
                    WHERE timestamp IS NOT NULL
                    LIMIT 1
                """)
                date_info = cursor.fetchone()
            else:
                date_info = {'earliest': None, 'latest': None, 'unique_dates': 0}
            
            # Get symbol count if applicable
            symbol_count = 0
            if 'symbol' in columns:
                cursor.execute(f"SELECT COUNT(DISTINCT symbol) as count FROM {table_name}")
                symbol_count = cursor.fetchone()['count']
            elif 'coin_symbol' in columns:
                cursor.execute(f"SELECT COUNT(DISTINCT coin_symbol) as count FROM {table_name}")
                symbol_count = cursor.fetchone()['count']
            
            # Recent data check (last 7 days)
            recent_data = 0
            if 'timestamp' in columns:
                cursor.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM {table_name} 
                    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """)
                recent_data = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'exists',
                'table': table_name,
                'collector': table_info['collector'],
                'row_count': row_count,
                'column_count': len(columns),
                'missing_critical_columns': list(missing_columns),
                'schema_issues': len(missing_columns) > 0,
                'date_range': {
                    'earliest': date_info['earliest'],
                    'latest': date_info['latest'],
                    'unique_dates': date_info['unique_dates']
                },
                'symbol_count': symbol_count,
                'recent_data_count': recent_data,
                'has_recent_data': recent_data > 0
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'table': table_name,
                'error': str(e)
            }

    def check_collector_exists(self, collector_name):
        """Check if collector file exists and has basic backfill features"""
        # Common paths to check
        paths_to_check = [
            f"services/price-collection/{collector_name}",
            f"services/onchain-collection/{collector_name}",
            f"services/news-collection/{collector_name}",
            f"services/sentiment-collection/{collector_name}",
            f"services/macro-collection/{collector_name}",
            collector_name  # Direct path
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Check for basic backfill capabilities
                    has_date_params = any(term in content for term in ['start_date', 'end_date', 'from_date', 'to_date'])
                    has_symbol_iteration = any(term in content for term in ['for symbol', 'symbols', 'crypto_symbols'])
                    has_db_writes = any(term in content for term in ['INSERT', 'UPDATE', 'cursor.execute'])
                    has_error_handling = 'try:' in content and 'except' in content
                    
                    backfill_capable = has_date_params and has_symbol_iteration and has_db_writes
                    
                    return {
                        'exists': True,
                        'path': path,
                        'backfill_capable': backfill_capable,
                        'has_date_params': has_date_params,
                        'has_symbol_iteration': has_symbol_iteration,
                        'has_db_writes': has_db_writes,
                        'has_error_handling': has_error_handling
                    }
                    
                except Exception as e:
                    return {'exists': True, 'path': path, 'error': str(e)}
        
        return {'exists': False, 'collector': collector_name}

    def run_quick_assessment(self):
        """Run quick assessment of all key tables"""
        print("QUICK COLLECTOR TABLE ASSESSMENT")
        print("=" * 50)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'analysis_date': datetime.now().isoformat(),
            'tables_analyzed': len(self.key_tables),
            'table_results': {},
            'collector_results': {},
            'summary': {
                'tables_missing': 0,
                'tables_with_schema_issues': 0,
                'tables_with_no_recent_data': 0,
                'collectors_missing': 0,
                'collectors_not_backfill_capable': 0
            }
        }
        
        # Analyze each table
        for table_name, table_info in self.key_tables.items():
            print(f"Checking table: {table_name}")
            
            # Table analysis
            table_result = self.check_table_status(table_name, table_info)
            results['table_results'][table_name] = table_result
            
            # Update summary
            if table_result['status'] == 'missing':
                results['summary']['tables_missing'] += 1
                print(f"  ❌ TABLE MISSING: {table_name}")
            elif table_result['status'] == 'error':
                print(f"  ⚠️  ERROR: {table_result.get('error', 'Unknown error')}")
            else:
                # Table exists
                issues = []
                
                if table_result.get('schema_issues'):
                    results['summary']['tables_with_schema_issues'] += 1
                    missing = table_result['missing_critical_columns']
                    issues.append(f"Missing columns: {', '.join(missing)}")
                
                if not table_result.get('has_recent_data'):
                    results['summary']['tables_with_no_recent_data'] += 1
                    issues.append("No recent data (last 7 days)")
                
                if issues:
                    print(f"  ⚠️  ISSUES: {'; '.join(issues)}")
                    print(f"      Rows: {table_result['row_count']:,}")
                    print(f"      Symbols: {table_result['symbol_count']}")
                    print(f"      Date range: {table_result['date_range']['earliest']} to {table_result['date_range']['latest']}")
                else:
                    print(f"  ✅ OK - {table_result['row_count']:,} rows, {table_result['symbol_count']} symbols")
            
            # Collector analysis
            collector_name = table_info['collector']
            if collector_name not in results['collector_results']:
                print(f"  Checking collector: {collector_name}")
                collector_result = self.check_collector_exists(collector_name)
                results['collector_results'][collector_name] = collector_result
                
                if not collector_result['exists']:
                    results['summary']['collectors_missing'] += 1
                    print(f"    ❌ COLLECTOR MISSING")
                elif not collector_result.get('backfill_capable', False):
                    results['summary']['collectors_not_backfill_capable'] += 1
                    print(f"    ⚠️  NOT BACKFILL CAPABLE")
                    print(f"       Path: {collector_result.get('path', 'unknown')}")
                    print(f"       Has date params: {collector_result.get('has_date_params', False)}")
                    print(f"       Has symbol iteration: {collector_result.get('has_symbol_iteration', False)}")
                else:
                    print(f"    ✅ BACKFILL CAPABLE ({collector_result['path']})")
            
            print()
        
        # Print summary
        print("SUMMARY")
        print("-" * 20)
        print(f"Tables analyzed: {results['tables_analyzed']}")
        print(f"Missing tables: {results['summary']['tables_missing']}")
        print(f"Tables with schema issues: {results['summary']['tables_with_schema_issues']}")
        print(f"Tables with no recent data: {results['summary']['tables_with_no_recent_data']}")
        print(f"Missing collectors: {results['summary']['collectors_missing']}")
        print(f"Collectors not backfill capable: {results['summary']['collectors_not_backfill_capable']}")
        print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_assessment_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Results saved to: {filename}")
        
        return results

if __name__ == "__main__":
    assessor = QuickTableAssessment()
    results = assessor.run_quick_assessment()