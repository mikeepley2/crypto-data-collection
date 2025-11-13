#!/usr/bin/env python3
"""
Collector Table Gap Analysis and Backfill Assessment
===================================================
Examines each collector table to identify:
1. Missing columns/fields
2. Data gaps (missing rows/dates)
3. Collector backfill capabilities
4. Required enhancements for complete backfill
"""

import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import logging
import json
import sys
import os
from collections import defaultdict
import warnings

# Add shared directory for dynamic symbol management
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
try:
    from table_config import (
        get_collector_symbols,
        get_supported_symbols,
        validate_symbol_exists
    )
    DYNAMIC_SYMBOLS_AVAILABLE = True
except ImportError:
    DYNAMIC_SYMBOLS_AVAILABLE = False

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collector_gap_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('collector-gap-analysis')

class CollectorGapAnalysis:
    """Analyze all collector tables for gaps and backfill needs"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', '172.22.32.1'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'autocommit': True,
            'charset': 'utf8mb4'
        }
        
        # Define collector tables with their requirements
        self.collector_tables = {
            'price_data': {
                'table': 'crypto_prices.price_data_real',
                'collector_path': 'services/price-collection/enhanced_crypto_prices_service.py',
                'symbol_column': 'symbol',
                'timestamp_column': 'timestamp',
                'frequency': 'hourly',
                'critical_columns': ['symbol', 'timestamp', 'price_usd', 'volume_24h', 'market_cap'],
                'optional_columns': ['volume_change_24h', 'price_change_24h', 'circulating_supply', 'ath', 'atl']
            },
            'technical_indicators': {
                'table': 'crypto_prices.technical_indicators',
                'collector_path': 'services/price-collection/enhanced_crypto_prices_service.py',
                'symbol_column': 'symbol',
                'timestamp_column': 'timestamp',
                'frequency': 'hourly',
                'critical_columns': ['symbol', 'timestamp', 'sma_20', 'ema_20', 'rsi'],
                'optional_columns': ['sma_50', 'ema_50', 'macd', 'bollinger_upper', 'bollinger_lower', 'volume_sma']
            },
            'onchain_data': {
                'table': 'crypto_prices.crypto_onchain_data',
                'collector_path': 'services/onchain-collection/onchain_collector_free.py',
                'symbol_column': 'coin_symbol',
                'timestamp_column': 'timestamp',
                'frequency': 'daily',
                'critical_columns': ['coin_symbol', 'timestamp', 'active_addresses', 'transaction_count'],
                'optional_columns': ['network_hash_rate', 'difficulty', 'fees_total', 'nvt_ratio']
            },
            'news_data': {
                'table': 'crypto_news.news_data',
                'collector_path': 'services/news-collection/crypto_news_collector.py',
                'symbol_column': None,  # News is general
                'timestamp_column': 'published_date',
                'frequency': 'continuous',
                'critical_columns': ['title', 'url', 'published_date', 'source'],
                'optional_columns': ['sentiment_score', 'sentiment_label', 'crypto_mentions', 'impact_score']
            },
            'sentiment_signals': {
                'table': 'crypto_prices.real_time_sentiment_signals',
                'collector_path': 'services/sentiment-collection/sentiment_aggregator.py',
                'symbol_column': 'symbol',
                'timestamp_column': 'timestamp',
                'frequency': 'hourly',
                'critical_columns': ['symbol', 'timestamp', 'sentiment_score', 'confidence'],
                'optional_columns': ['news_sentiment', 'social_sentiment', 'volume_weighted_sentiment']
            },
            'ohlc_data': {
                'table': 'crypto_prices.ohlc_data',
                'collector_path': 'services/price-collection/enhanced_crypto_prices_service.py',
                'symbol_column': 'symbol',
                'timestamp_column': 'timestamp',
                'frequency': 'hourly',
                'critical_columns': ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume'],
                'optional_columns': ['volume_weighted_price', 'trades_count', 'taker_buy_volume']
            },
            'macro_indicators': {
                'table': 'crypto_prices.macro_indicators',
                'collector_path': 'services/macro-collection/macro_data_collector.py',
                'symbol_column': None,  # Macro is market-wide
                'timestamp_column': 'timestamp',
                'frequency': 'daily',
                'critical_columns': ['timestamp', 'indicator_name', 'value'],
                'optional_columns': ['indicator_type', 'source', 'unit', 'seasonal_adjustment']
            }
        }
        
        # Analysis parameters
        self.analysis_start_date = date(2023, 1, 1)
        self.analysis_end_date = date.today()
        self.total_days = (self.analysis_end_date - self.analysis_start_date).days
        
        # Get active symbols
        self.active_symbols = self._get_active_symbols()
        
        logger.info(f"🔍 Collector Gap Analysis initialized")
        logger.info(f"   Tables to analyze: {len(self.collector_tables)}")
        logger.info(f"   Date range: {self.analysis_start_date} to {self.analysis_end_date} ({self.total_days} days)")
        logger.info(f"   Active symbols: {len(self.active_symbols)}")

    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)

    def _get_active_symbols(self):
        """Get list of active crypto symbols"""
        if DYNAMIC_SYMBOLS_AVAILABLE:
            try:
                symbols = get_collector_symbols(collector_type='price')
                logger.info(f"Loaded {len(symbols)} symbols from crypto_assets table")
                return symbols
            except Exception as e:
                logger.warning(f"Failed to get dynamic symbols: {e}")
        
        # Fallback: query crypto_assets directly
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY symbol")
            symbols = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            logger.info(f"Loaded {len(symbols)} symbols from database query")
            return symbols
        except Exception as e:
            logger.error(f"Failed to get symbols from database: {e}")
            return ['BTC', 'ETH', 'ADA', 'SOL']  # Ultimate fallback

    def check_table_exists(self, table_name):
        """Check if table exists and get basic info"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check if table exists
            database, table = table_name.split('.')
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{database}' 
                AND table_name = '{table}'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.close()
                conn.close()
                return {'exists': False}
            
            # Get table info
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return {
                'exists': True,
                'row_count': row_count,
                'columns': columns,
                'column_count': len(columns)
            }
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def analyze_schema_completeness(self, table_name, table_config):
        """Analyze if table has all required columns"""
        table_info = self.check_table_exists(table_name)
        
        if not table_info['exists']:
            return {
                'table': table_name,
                'status': 'missing',
                'error': table_info.get('error', 'Table does not exist')
            }
        
        actual_columns = set(table_info['columns'])
        required_columns = set(table_config['critical_columns'])
        optional_columns = set(table_config['optional_columns'])
        all_expected = required_columns | optional_columns
        
        missing_critical = required_columns - actual_columns
        missing_optional = optional_columns - actual_columns
        extra_columns = actual_columns - all_expected
        
        completeness_score = len(actual_columns & all_expected) / len(all_expected) * 100
        
        return {
            'table': table_name,
            'status': 'exists',
            'row_count': table_info['row_count'],
            'schema_analysis': {
                'total_columns': len(actual_columns),
                'required_columns_present': len(required_columns - missing_critical),
                'optional_columns_present': len(optional_columns - missing_optional),
                'missing_critical': list(missing_critical),
                'missing_optional': list(missing_optional),
                'extra_columns': list(extra_columns),
                'completeness_score': round(completeness_score, 2)
            },
            'schema_issues': len(missing_critical) > 0
        }

    def analyze_data_completeness(self, table_name, table_config):
        """Analyze data completeness - missing dates/symbols"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            symbol_column = table_config['symbol_column']
            timestamp_column = table_config['timestamp_column']
            frequency = table_config['frequency']
            
            # Get basic date range info
            cursor.execute(f"""
                SELECT 
                    MIN({timestamp_column}) as earliest_date,
                    MAX({timestamp_column}) as latest_date,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT DATE({timestamp_column})) as unique_dates
                FROM {table_name}
                WHERE {timestamp_column} IS NOT NULL
            """)
            date_info = cursor.fetchone()
            
            analysis = {
                'table': table_name,
                'total_records': date_info['total_records'],
                'date_range': {
                    'earliest': date_info['earliest_date'],
                    'latest': date_info['latest_date'],
                    'unique_dates': date_info['unique_dates']
                }
            }
            
            if symbol_column:
                # Symbol-specific analysis
                cursor.execute(f"""
                    SELECT 
                        {symbol_column} as symbol,
                        COUNT(*) as record_count,
                        MIN({timestamp_column}) as first_record,
                        MAX({timestamp_column}) as last_record,
                        COUNT(DISTINCT DATE({timestamp_column})) as unique_dates
                    FROM {table_name}
                    WHERE {symbol_column} IS NOT NULL
                    GROUP BY {symbol_column}
                    ORDER BY record_count DESC
                """)
                symbol_stats = cursor.fetchall()
                
                # Calculate expected records
                expected_records_per_symbol = self._calculate_expected_records(frequency)
                
                symbol_analysis = []
                symbols_with_data = set()
                
                for stats in symbol_stats:
                    symbol = stats['symbol']
                    symbols_with_data.add(symbol)
                    
                    completeness = (stats['record_count'] / expected_records_per_symbol) * 100
                    
                    # Check for recent data (last 7 days)
                    cursor.execute(f"""
                        SELECT COUNT(*) as recent_count
                        FROM {table_name}
                        WHERE {symbol_column} = %s
                        AND {timestamp_column} >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    """, (symbol,))
                    recent_data = cursor.fetchone()['recent_count']
                    
                    symbol_analysis.append({
                        'symbol': symbol,
                        'total_records': stats['record_count'],
                        'expected_records': expected_records_per_symbol,
                        'completeness_percent': round(completeness, 2),
                        'first_record': stats['first_record'],
                        'last_record': stats['last_record'],
                        'unique_dates': stats['unique_dates'],
                        'recent_data_count': recent_data,
                        'has_recent_data': recent_data > 0
                    })
                
                # Find missing symbols
                missing_symbols = set(self.active_symbols) - symbols_with_data
                
                analysis['symbol_analysis'] = {
                    'symbols_with_data': len(symbol_stats),
                    'expected_symbols': len(self.active_symbols),
                    'missing_symbols': list(missing_symbols),
                    'symbol_details': symbol_analysis
                }
                
                # Identify symbols with low completeness
                low_completeness = [s for s in symbol_analysis if s['completeness_percent'] < 50]
                stale_data = [s for s in symbol_analysis if not s['has_recent_data']]
                
                analysis['data_issues'] = {
                    'missing_symbol_count': len(missing_symbols),
                    'low_completeness_count': len(low_completeness),
                    'stale_data_count': len(stale_data),
                    'critical_issues': len(missing_symbols) > 0 or len(low_completeness) > 0
                }
            
            cursor.close()
            conn.close()
            
            return analysis
            
        except Exception as e:
            return {
                'table': table_name,
                'error': str(e)
            }

    def _calculate_expected_records(self, frequency):
        """Calculate expected number of records based on frequency"""
        if frequency == 'hourly':
            return self.total_days * 24
        elif frequency == 'daily':
            return self.total_days
        elif frequency == 'continuous':
            # For news, expect at least daily coverage
            return self.total_days
        else:
            return self.total_days

    def evaluate_collector_backfill_capability(self, collector_path):
        """Evaluate if collector can handle historical backfill"""
        
        if not os.path.exists(collector_path):
            return {
                'collector_path': collector_path,
                'exists': False,
                'backfill_capable': False,
                'issues': ['Collector file not found']
            }
        
        try:
            with open(collector_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for backfill capabilities
            capabilities = {
                'date_range_params': any(term in content for term in ['start_date', 'end_date', 'from_date', 'to_date']),
                'historical_mode': any(term in content.lower() for term in ['historical', 'history', 'backfill']),
                'pagination_support': any(term in content.lower() for term in ['page', 'limit', 'offset', 'cursor']),
                'rate_limiting': any(term in content for term in ['sleep', 'time.sleep', 'rate_limit', 'throttle']),
                'error_handling': 'try:' in content and 'except' in content,
                'database_writes': any(term in content for term in ['INSERT', 'UPDATE', 'cursor.execute']),
                'symbol_iteration': any(term in content for term in ['for symbol', 'symbols', 'crypto_symbols']),
                'async_support': 'async' in content or 'await' in content,
                'batch_processing': any(term in content.lower() for term in ['batch', 'bulk', 'executemany'])
            }
            
            # Calculate backfill score
            score = sum(capabilities.values()) / len(capabilities) * 100
            
            # Determine if backfill capable
            essential_features = ['date_range_params', 'database_writes', 'symbol_iteration', 'error_handling']
            backfill_capable = all(capabilities[feature] for feature in essential_features)
            
            # Identify missing features for backfill
            missing_features = [feature for feature, present in capabilities.items() if not present]
            
            return {
                'collector_path': collector_path,
                'exists': True,
                'backfill_capable': backfill_capable,
                'backfill_score': round(score, 2),
                'capabilities': capabilities,
                'missing_features': missing_features,
                'issues': missing_features if missing_features else []
            }
            
        except Exception as e:
            return {
                'collector_path': collector_path,
                'exists': True,
                'error': str(e),
                'backfill_capable': False,
                'issues': [f'Error analyzing collector: {str(e)}']
            }

    def generate_backfill_plan(self, analysis_results):
        """Generate specific backfill plan for each table"""
        backfill_plan = {}
        
        for table_type, results in analysis_results.items():
            table_config = self.collector_tables[table_type]
            
            plan = {
                'table': table_config['table'],
                'collector': table_config['collector_path'],
                'priority': 'LOW',
                'actions': [],
                'estimated_effort': 'Low'
            }
            
            # Check schema issues
            if results.get('schema_analysis', {}).get('schema_issues'):
                schema = results['schema_analysis']
                if schema['missing_critical']:
                    plan['priority'] = 'HIGH'
                    plan['actions'].append({
                        'type': 'schema_fix',
                        'action': f"Add missing critical columns: {', '.join(schema['missing_critical'])}",
                        'effort': 'Medium'
                    })
            
            # Check data issues
            if 'data_analysis' in results and 'data_issues' in results['data_analysis']:
                data_issues = results['data_analysis']['data_issues']
                
                if data_issues['missing_symbol_count'] > 0:
                    plan['priority'] = 'HIGH' if data_issues['missing_symbol_count'] > 10 else 'MEDIUM'
                    plan['actions'].append({
                        'type': 'symbol_backfill',
                        'action': f"Backfill data for {data_issues['missing_symbol_count']} missing symbols",
                        'effort': 'High' if data_issues['missing_symbol_count'] > 20 else 'Medium'
                    })
                
                if data_issues['low_completeness_count'] > 0:
                    plan['actions'].append({
                        'type': 'completeness_backfill',
                        'action': f"Improve completeness for {data_issues['low_completeness_count']} symbols",
                        'effort': 'Medium'
                    })
                
                if data_issues['stale_data_count'] > 0:
                    plan['actions'].append({
                        'type': 'recent_data_fix',
                        'action': f"Fix recent data collection for {data_issues['stale_data_count']} symbols",
                        'effort': 'Low'
                    })
            
            # Check collector issues
            if 'collector_analysis' in results:
                collector = results['collector_analysis']
                
                if not collector.get('backfill_capable'):
                    plan['priority'] = 'HIGH'
                    plan['actions'].append({
                        'type': 'collector_enhancement',
                        'action': 'Enhance collector to support historical backfill',
                        'effort': 'High',
                        'missing_features': collector.get('missing_features', [])
                    })
                
                elif collector.get('backfill_score', 0) < 70:
                    plan['actions'].append({
                        'type': 'collector_improvement',
                        'action': 'Improve collector reliability and features',
                        'effort': 'Medium'
                    })
            
            # Estimate overall effort
            if plan['actions']:
                effort_levels = [action.get('effort', 'Low') for action in plan['actions']]
                if 'High' in effort_levels:
                    plan['estimated_effort'] = 'High'
                elif 'Medium' in effort_levels:
                    plan['estimated_effort'] = 'Medium'
            
            # Set priority based on issues
            if plan['priority'] == 'LOW' and plan['actions']:
                plan['priority'] = 'MEDIUM'
            
            backfill_plan[table_type] = plan
        
        return backfill_plan

    def run_complete_analysis(self):
        """Run comprehensive gap analysis for all collector tables"""
        logger.info("🚀 STARTING COMPREHENSIVE COLLECTOR GAP ANALYSIS")
        logger.info("=" * 60)
        
        analysis_results = {}
        
        for table_type, table_config in self.collector_tables.items():
            table_name = table_config['table']
            collector_path = table_config['collector_path']
            
            logger.info(f"\n📊 Analyzing: {table_type}")
            logger.info(f"   Table: {table_name}")
            logger.info(f"   Collector: {collector_path}")
            
            results = {}
            
            # 1. Schema Analysis
            logger.info("   🔍 Checking schema completeness...")
            results['schema_analysis'] = self.analyze_schema_completeness(table_name, table_config)
            
            # 2. Data Completeness Analysis
            if results['schema_analysis']['status'] == 'exists':
                logger.info("   📈 Analyzing data completeness...")
                results['data_analysis'] = self.analyze_data_completeness(table_name, table_config)
            
            # 3. Collector Capability Analysis
            logger.info("   🔧 Evaluating collector capabilities...")
            results['collector_analysis'] = self.evaluate_collector_backfill_capability(collector_path)
            
            analysis_results[table_type] = results
            
            # Quick status summary
            schema_ok = not results['schema_analysis'].get('schema_issues', True)
            data_ok = not results.get('data_analysis', {}).get('data_issues', {}).get('critical_issues', True)
            collector_ok = results['collector_analysis'].get('backfill_capable', False)
            
            status = "✅" if schema_ok and data_ok and collector_ok else "⚠️"
            logger.info(f"   {status} Status: Schema OK: {schema_ok}, Data OK: {data_ok}, Collector OK: {collector_ok}")
        
        # Generate backfill plan
        logger.info("\n💡 Generating backfill execution plan...")
        backfill_plan = self.generate_backfill_plan(analysis_results)
        
        # Summary statistics
        total_issues = sum(len(plan['actions']) for plan in backfill_plan.values())
        high_priority = sum(1 for plan in backfill_plan.values() if plan['priority'] == 'HIGH')
        
        logger.info(f"\n📋 ANALYSIS SUMMARY:")
        logger.info(f"   Tables analyzed: {len(self.collector_tables)}")
        logger.info(f"   Total issues found: {total_issues}")
        logger.info(f"   High priority tables: {high_priority}")
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': {
                'tables_analyzed': len(self.collector_tables),
                'active_symbols': len(self.active_symbols),
                'analysis_period': f"{self.analysis_start_date} to {self.analysis_end_date}",
                'total_issues': total_issues,
                'high_priority_issues': high_priority
            },
            'detailed_analysis': analysis_results,
            'backfill_plan': backfill_plan
        }

    def save_analysis_results(self, results):
        """Save analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON results
        json_filename = f"collector_gap_analysis_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save markdown summary
        md_filename = f"collector_gap_summary_{timestamp}.md"
        self._create_markdown_summary(results, md_filename)
        
        logger.info(f"📄 Results saved:")
        logger.info(f"   Detailed: {json_filename}")
        logger.info(f"   Summary: {md_filename}")
        
        return json_filename, md_filename

    def _create_markdown_summary(self, results, filename):
        """Create markdown summary report"""
        with open(filename, 'w') as f:
            f.write("# Collector Gap Analysis Report\n\n")
            f.write(f"**Analysis Date:** {results['analysis_timestamp']}\n")
            f.write(f"**Tables Analyzed:** {results['summary']['tables_analyzed']}\n")
            f.write(f"**Active Symbols:** {results['summary']['active_symbols']}\n")
            f.write(f"**Period:** {results['summary']['analysis_period']}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Issues:** {results['summary']['total_issues']}\n")
            f.write(f"- **High Priority:** {results['summary']['high_priority_issues']}\n\n")
            
            f.write("## Backfill Execution Plan\n\n")
            
            for table_type, plan in results['backfill_plan'].items():
                f.write(f"### {table_type.title().replace('_', ' ')}\n")
                f.write(f"**Priority:** {plan['priority']}\n")
                f.write(f"**Table:** `{plan['table']}`\n")
                f.write(f"**Collector:** `{plan['collector']}`\n")
                f.write(f"**Estimated Effort:** {plan['estimated_effort']}\n\n")
                
                if plan['actions']:
                    f.write("**Required Actions:**\n")
                    for i, action in enumerate(plan['actions'], 1):
                        f.write(f"{i}. **{action['type'].replace('_', ' ').title()}**: {action['action']}\n")
                        f.write(f"   - Effort: {action['effort']}\n")
                    f.write("\n")
                else:
                    f.write("✅ No issues found - table is complete.\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Address HIGH priority issues first\n")
            f.write("2. Enhance collectors lacking backfill capabilities\n")
            f.write("3. Execute schema fixes before data backfills\n")
            f.write("4. Run targeted backfills for missing data\n")
            f.write("5. Implement monitoring for ongoing data completeness\n")

if __name__ == "__main__":
    analyzer = CollectorGapAnalysis()
    results = analyzer.run_complete_analysis()
    analyzer.save_analysis_results(results)
    
    logger.info("\n🎉 COLLECTOR GAP ANALYSIS COMPLETE!")
    logger.info("Check the generated files for detailed results and action plan.")