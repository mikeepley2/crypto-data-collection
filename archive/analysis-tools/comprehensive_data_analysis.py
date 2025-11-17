#!/usr/bin/env python3
"""
Comprehensive Data Quality Analysis for ML/Signal Generation
Analyzes all 7 collectors' target tables for completeness, quality, and ML readiness
"""

import os
import sys
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("data-quality-analyzer")

class DataQualityAnalyzer:
    """Comprehensive data quality analyzer for all collector tables"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', '172.22.32.1'),
            'user': os.getenv('DB_USER', 'news_collector'),
            'password': os.getenv('DB_PASSWORD', '99Rules!'),
            'database': os.getenv('DB_NAME', 'crypto_prices'),
        }
        
        # Define all collector target tables
        self.collector_tables = {
            'technical_indicators': {
                'collector': 'Enhanced Technical Calculator',
                'k8s_file': 'k8s/enhanced-technical-calculator.yaml',
                'primary_key': ['symbol', 'timestamp_iso'],
                'critical_columns': ['symbol', 'timestamp_iso', 'sma_20', 'rsi_14', 'macd_line', 'bb_upper', 'bb_lower'],
                'ml_features': ['sma_10', 'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26', 'rsi', 'rsi_14', 'macd', 'macd_signal', 'bb_upper', 'bb_middle', 'bb_lower', 'atr'],
                'frequency': '2 hours',
                'data_source': 'ohlc_data'
            },
            'macro_indicators': {
                'collector': 'Enhanced Macro Collector',
                'k8s_file': 'k8s/enhanced-macro-collector-deployment.yaml',
                'primary_key': ['indicator_name', 'indicator_date'],
                'critical_columns': ['indicator_name', 'indicator_date', 'value', 'frequency'],
                'ml_features': ['value'],  # Pivoted by indicator_name
                'frequency': 'Daily/Monthly/Quarterly',
                'data_source': 'FRED API'
            },
            'crypto_prices': {
                'collector': 'Enhanced Crypto Prices Collector',
                'k8s_file': 'k8s/collectors/enhanced-crypto-prices-automatic.yaml',
                'primary_key': ['symbol', 'timestamp'],
                'critical_columns': ['symbol', 'timestamp', 'current_price', 'market_cap', 'volume_24h'],
                'ml_features': ['current_price', 'market_cap', 'volume_24h', 'price_change_24h', 'volume_usd_24h'],
                'frequency': '5 minutes',
                'data_source': 'CoinGecko/Coinbase APIs'
            },
            'crypto_news': {
                'collector': 'News Collector + Enhanced Sentiment Collector',
                'k8s_file': 'k8s/news-collector-deployment.yaml + k8s/fix-sentiment-collector.yaml',
                'primary_key': ['id'],
                'critical_columns': ['id', 'title', 'published_at', 'sentiment_score'],
                'ml_features': ['sentiment_score', 'sentiment_magnitude', 'compound_sentiment', 'positive_score', 'negative_score', 'neutral_score'],
                'frequency': '30 minutes',
                'data_source': 'News APIs'
            },
            'ohlc_data': {
                'collector': 'OHLC Collector',
                'k8s_file': 'k8s/ohlc-collector-deployment.yaml',
                'primary_key': ['symbol', 'timestamp_iso'],
                'critical_columns': ['symbol', 'timestamp_iso', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'],
                'ml_features': ['open_price', 'high_price', 'low_price', 'close_price', 'volume'],
                'frequency': 'Hourly',
                'data_source': 'CoinGecko API'
            },
            'crypto_onchain_data': {
                'collector': 'Onchain Collector',
                'k8s_file': 'k8s/onchain-collector-deployment.yaml',
                'primary_key': ['asset_id', 'timestamp'],
                'critical_columns': ['asset_id', 'timestamp', 'active_addresses', 'transaction_count', 'volume_usd'],
                'ml_features': ['active_addresses', 'transaction_count', 'volume_usd', 'network_hash_rate', 'market_cap_rank'],
                'frequency': '4 hours',
                'data_source': 'Multiple APIs'
            },
            'price_data_real': {
                'collector': 'Enhanced Crypto Prices Collector (alternative table)',
                'k8s_file': 'k8s/collectors/enhanced-crypto-prices-automatic.yaml',
                'primary_key': ['symbol', 'timestamp'],
                'critical_columns': ['symbol', 'timestamp', 'current_price', 'high_24h', 'low_24h', 'volume_usd_24h'],
                'ml_features': ['current_price', 'high_24h', 'low_24h', 'volume_usd_24h', 'market_cap', 'circulating_supply'],
                'frequency': '5 minutes',
                'data_source': 'CoinGecko/Coinbase APIs'
            }
        }
        
        logger.info(f"🔍 Initialized analyzer for {len(self.collector_tables)} collector tables")
    
    def get_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def analyze_table_basic_stats(self, table_name: str) -> Dict:
        """Get basic statistics for a table"""
        conn = self.get_connection()
        if not conn:
            return {'error': 'No database connection'}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE %s", (table_name,))
            if not cursor.fetchone():
                return {'error': 'Table does not exist'}
            
            # Get basic stats
            stats = {}
            
            # Row count
            cursor.execute(f"SELECT COUNT(*) as total_rows FROM {table_name}")
            stats['total_rows'] = cursor.fetchone()['total_rows']
            
            # Get table schema
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            stats['total_columns'] = len(columns)
            stats['columns'] = [col['Field'] for col in columns]
            
            # Get date range if timestamp columns exist
            timestamp_cols = ['timestamp', 'timestamp_iso', 'published_at', 'indicator_date', 'collected_at', 'created_at']
            found_timestamp_col = None
            
            for ts_col in timestamp_cols:
                if ts_col in stats['columns']:
                    found_timestamp_col = ts_col
                    break
            
            if found_timestamp_col:
                cursor.execute(f"SELECT MIN({found_timestamp_col}) as min_date, MAX({found_timestamp_col}) as max_date FROM {table_name}")
                date_range = cursor.fetchone()
                stats['date_range'] = {
                    'min_date': date_range['min_date'],
                    'max_date': date_range['max_date'],
                    'timestamp_column': found_timestamp_col
                }
                
                if date_range['max_date']:
                    days_covered = (date_range['max_date'] - date_range['min_date']).days if date_range['min_date'] else 0
                    stats['days_covered'] = days_covered
            
            # Get unique symbols/assets if applicable
            symbol_cols = ['symbol', 'asset_id', 'indicator_name']
            found_symbol_col = None
            
            for sym_col in symbol_cols:
                if sym_col in stats['columns']:
                    found_symbol_col = sym_col
                    break
            
            if found_symbol_col:
                cursor.execute(f"SELECT COUNT(DISTINCT {found_symbol_col}) as unique_symbols FROM {table_name}")
                stats['unique_symbols'] = cursor.fetchone()['unique_symbols']
                
                # Get sample symbols
                cursor.execute(f"SELECT DISTINCT {found_symbol_col} FROM {table_name} LIMIT 10")
                stats['sample_symbols'] = [row[found_symbol_col] for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing {table_name}: {e}")
            return {'error': str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def analyze_data_quality(self, table_name: str, config: Dict) -> Dict:
        """Analyze data quality for ML readiness"""
        conn = self.get_connection()
        if not conn:
            return {'error': 'No database connection'}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            quality_metrics = {}
            
            # Check critical columns existence and null rates
            for col in config['critical_columns']:
                try:
                    # Check if column exists
                    cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                    total_rows = cursor.fetchone()['total']
                    
                    if total_rows > 0:
                        # Check null rate
                        cursor.execute(f"SELECT COUNT(*) as null_count FROM {table_name} WHERE {col} IS NULL")
                        null_count = cursor.fetchone()['null_count']
                        null_rate = (null_count / total_rows) * 100
                        
                        quality_metrics[col] = {
                            'exists': True,
                            'null_rate': null_rate,
                            'null_count': null_count,
                            'total_rows': total_rows
                        }
                    else:
                        quality_metrics[col] = {'exists': True, 'null_rate': 100, 'total_rows': 0}
                        
                except Exception as e:
                    quality_metrics[col] = {'exists': False, 'error': str(e)}
            
            # Check ML feature columns
            ml_quality = {}
            for feature in config['ml_features']:
                try:
                    cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                    total_rows = cursor.fetchone()['total']
                    
                    if total_rows > 0:
                        # Check if column exists first
                        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{feature}'")
                        if cursor.fetchone():
                            # Check null rate and basic stats
                            cursor.execute(f"SELECT COUNT(*) as null_count, AVG({feature}) as avg_val, MIN({feature}) as min_val, MAX({feature}) as max_val FROM {table_name} WHERE {feature} IS NOT NULL")
                            result = cursor.fetchone()
                            
                            null_count = total_rows - (total_rows - result['null_count']) if result['null_count'] else 0
                            null_rate = (null_count / total_rows) * 100
                            
                            ml_quality[feature] = {
                                'exists': True,
                                'null_rate': null_rate,
                                'avg_value': float(result['avg_val']) if result['avg_val'] else None,
                                'min_value': float(result['min_val']) if result['min_val'] else None,
                                'max_value': float(result['max_val']) if result['max_val'] else None,
                                'data_points': total_rows - null_count
                            }
                        else:
                            ml_quality[feature] = {'exists': False, 'error': 'Column not found'}
                    else:
                        ml_quality[feature] = {'exists': True, 'null_rate': 100, 'data_points': 0}
                        
                except Exception as e:
                    ml_quality[feature] = {'exists': False, 'error': str(e)}
            
            quality_metrics['ml_features'] = ml_quality
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing data quality for {table_name}: {e}")
            return {'error': str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def analyze_data_freshness(self, table_name: str, config: Dict) -> Dict:
        """Analyze data freshness and collection gaps"""
        conn = self.get_connection()
        if not conn:
            return {'error': 'No database connection'}
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            freshness_metrics = {}
            
            # Find timestamp column
            timestamp_cols = ['timestamp', 'timestamp_iso', 'published_at', 'indicator_date', 'collected_at', 'created_at']
            found_timestamp_col = None
            
            cursor.execute(f"DESCRIBE {table_name}")
            table_columns = [col['Field'] for col in cursor.fetchall()]
            
            for ts_col in timestamp_cols:
                if ts_col in table_columns:
                    found_timestamp_col = ts_col
                    break
            
            if not found_timestamp_col:
                return {'error': 'No timestamp column found'}
            
            # Get latest data
            cursor.execute(f"SELECT MAX({found_timestamp_col}) as latest_timestamp FROM {table_name}")
            latest = cursor.fetchone()['latest_timestamp']
            
            if latest:
                now = datetime.now()
                if isinstance(latest, datetime):
                    hours_behind = (now - latest).total_seconds() / 3600
                else:
                    # Handle date-only fields
                    latest_datetime = datetime.combine(latest, datetime.min.time())
                    hours_behind = (now - latest_datetime).total_seconds() / 3600
                
                freshness_metrics['latest_timestamp'] = latest
                freshness_metrics['hours_behind'] = hours_behind
                freshness_metrics['timestamp_column'] = found_timestamp_col
                
                # Categorize freshness
                if hours_behind <= 1:
                    freshness_metrics['freshness_status'] = 'excellent'
                elif hours_behind <= 24:
                    freshness_metrics['freshness_status'] = 'good'
                elif hours_behind <= 168:  # 7 days
                    freshness_metrics['freshness_status'] = 'stale'
                else:
                    freshness_metrics['freshness_status'] = 'very_stale'
                
                # Check for symbols/assets if applicable
                symbol_cols = ['symbol', 'asset_id', 'indicator_name']
                found_symbol_col = None
                
                for sym_col in symbol_cols:
                    if sym_col in table_columns:
                        found_symbol_col = sym_col
                        break
                
                if found_symbol_col:
                    # Check freshness per symbol (last 24 hours)
                    cursor.execute(f"""
                        SELECT {found_symbol_col}, MAX({found_timestamp_col}) as latest 
                        FROM {table_name} 
                        WHERE {found_timestamp_col} >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                        GROUP BY {found_symbol_col}
                        ORDER BY latest DESC
                        LIMIT 20
                    """)
                    recent_symbols = cursor.fetchall()
                    freshness_metrics['recent_symbols'] = len(recent_symbols)
                    freshness_metrics['sample_recent_data'] = recent_symbols[:5]
            
            return freshness_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing freshness for {table_name}: {e}")
            return {'error': str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def calculate_ml_readiness_score(self, table_name: str, basic_stats: Dict, quality_metrics: Dict, freshness_metrics: Dict, config: Dict) -> Dict:
        """Calculate ML readiness score"""
        
        score_components = {
            'data_volume': 0,      # 0-25 points
            'data_quality': 0,     # 0-25 points  
            'data_freshness': 0,   # 0-25 points
            'feature_coverage': 0  # 0-25 points
        }
        
        # Data Volume Score (0-25)
        total_rows = basic_stats.get('total_rows', 0)
        if total_rows >= 100000:
            score_components['data_volume'] = 25
        elif total_rows >= 10000:
            score_components['data_volume'] = 20
        elif total_rows >= 1000:
            score_components['data_volume'] = 15
        elif total_rows >= 100:
            score_components['data_volume'] = 10
        else:
            score_components['data_volume'] = 5
        
        # Data Quality Score (0-25) - based on null rates in critical columns
        quality_score = 0
        if 'error' not in quality_metrics:
            critical_cols_quality = []
            for col in config['critical_columns']:
                if col in quality_metrics and 'null_rate' in quality_metrics[col]:
                    null_rate = quality_metrics[col]['null_rate']
                    if null_rate <= 5:
                        critical_cols_quality.append(25)
                    elif null_rate <= 15:
                        critical_cols_quality.append(20)
                    elif null_rate <= 30:
                        critical_cols_quality.append(15)
                    elif null_rate <= 50:
                        critical_cols_quality.append(10)
                    else:
                        critical_cols_quality.append(5)
            
            if critical_cols_quality:
                quality_score = sum(critical_cols_quality) / len(critical_cols_quality)
        
        score_components['data_quality'] = quality_score
        
        # Data Freshness Score (0-25)
        freshness_score = 0
        if 'error' not in freshness_metrics:
            freshness_status = freshness_metrics.get('freshness_status', 'very_stale')
            if freshness_status == 'excellent':
                freshness_score = 25
            elif freshness_status == 'good':
                freshness_score = 20
            elif freshness_status == 'stale':
                freshness_score = 10
            else:
                freshness_score = 5
        
        score_components['data_freshness'] = freshness_score
        
        # Feature Coverage Score (0-25) - ML features availability
        feature_score = 0
        if 'ml_features' in quality_metrics:
            ml_features = quality_metrics['ml_features']
            available_features = 0
            total_features = len(config['ml_features'])
            
            for feature in config['ml_features']:
                if feature in ml_features and ml_features[feature].get('exists', False):
                    null_rate = ml_features[feature].get('null_rate', 100)
                    if null_rate <= 20:  # Feature is usable if null rate <= 20%
                        available_features += 1
            
            if total_features > 0:
                feature_coverage = (available_features / total_features) * 100
                if feature_coverage >= 90:
                    feature_score = 25
                elif feature_coverage >= 70:
                    feature_score = 20
                elif feature_coverage >= 50:
                    feature_score = 15
                elif feature_coverage >= 30:
                    feature_score = 10
                else:
                    feature_score = 5
        
        score_components['feature_coverage'] = feature_score
        
        # Calculate total score
        total_score = sum(score_components.values())
        
        # Determine readiness level
        if total_score >= 80:
            readiness_level = 'excellent'
        elif total_score >= 60:
            readiness_level = 'good'
        elif total_score >= 40:
            readiness_level = 'fair'
        else:
            readiness_level = 'poor'
        
        return {
            'total_score': total_score,
            'readiness_level': readiness_level,
            'score_components': score_components,
            'recommendations': self.generate_recommendations(table_name, score_components, basic_stats, quality_metrics, freshness_metrics)
        }
    
    def generate_recommendations(self, table_name: str, score_components: Dict, basic_stats: Dict, quality_metrics: Dict, freshness_metrics: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Data volume recommendations
        if score_components['data_volume'] < 20:
            recommendations.append(f"📊 Increase data collection frequency - only {basic_stats.get('total_rows', 0)} records")
        
        # Data quality recommendations
        if score_components['data_quality'] < 20:
            recommendations.append("🔧 Address high null rates in critical columns")
            
        # Freshness recommendations
        if score_components['data_freshness'] < 15:
            freshness_status = freshness_metrics.get('freshness_status', 'unknown')
            hours_behind = freshness_metrics.get('hours_behind', 'unknown')
            recommendations.append(f"⏰ Improve data freshness - currently {freshness_status} ({hours_behind:.1f} hours behind)")
        
        # Feature coverage recommendations
        if score_components['feature_coverage'] < 20:
            recommendations.append("🎯 Improve ML feature availability - missing key features")
            
        return recommendations
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run comprehensive analysis on all collector tables"""
        logger.info("🚀 Starting comprehensive data quality analysis...")
        
        results = {}
        summary = {
            'total_tables': len(self.collector_tables),
            'tables_analyzed': 0,
            'ml_ready_tables': 0,
            'total_records': 0,
            'recommendations': []
        }
        
        for table_name, config in self.collector_tables.items():
            logger.info(f"📊 Analyzing {table_name}...")
            
            # Basic statistics
            basic_stats = self.analyze_table_basic_stats(table_name)
            
            if 'error' not in basic_stats:
                summary['tables_analyzed'] += 1
                summary['total_records'] += basic_stats.get('total_rows', 0)
                
                # Data quality analysis
                quality_metrics = self.analyze_data_quality(table_name, config)
                
                # Data freshness analysis  
                freshness_metrics = self.analyze_data_freshness(table_name, config)
                
                # ML readiness score
                ml_readiness = self.calculate_ml_readiness_score(table_name, basic_stats, quality_metrics, freshness_metrics, config)
                
                if ml_readiness['readiness_level'] in ['excellent', 'good']:
                    summary['ml_ready_tables'] += 1
                
                results[table_name] = {
                    'collector_info': config,
                    'basic_stats': basic_stats,
                    'quality_metrics': quality_metrics,
                    'freshness_metrics': freshness_metrics,
                    'ml_readiness': ml_readiness
                }
                
                # Add recommendations to summary
                summary['recommendations'].extend([f"{table_name}: {rec}" for rec in ml_readiness['recommendations']])
                
                logger.info(f"   ✅ {table_name}: {ml_readiness['readiness_level'].upper()} (Score: {ml_readiness['total_score']}/100)")
                
            else:
                logger.error(f"   ❌ {table_name}: {basic_stats['error']}")
                results[table_name] = {
                    'collector_info': config,
                    'error': basic_stats['error']
                }
        
        logger.info(f"📋 Analysis complete: {summary['tables_analyzed']}/{summary['total_tables']} tables analyzed")
        logger.info(f"🎯 ML Ready: {summary['ml_ready_tables']}/{summary['tables_analyzed']} tables")
        logger.info(f"📊 Total Records: {summary['total_records']:,}")
        
        return {
            'summary': summary,
            'detailed_results': results,
            'analysis_timestamp': datetime.now(),
            'analyzer_version': '1.0'
        }


def main():
    """Main execution function"""
    analyzer = DataQualityAnalyzer()
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Print summary report
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE DATA QUALITY ANALYSIS FOR ML/SIGNAL GENERATION")
    print("="*80)
    
    summary = results['summary']
    print(f"\n📊 OVERVIEW:")
    print(f"   Tables Analyzed: {summary['tables_analyzed']}/{summary['total_tables']}")
    print(f"   ML Ready Tables: {summary['ml_ready_tables']}/{summary['tables_analyzed']}")
    print(f"   Total Records: {summary['total_records']:,}")
    
    print(f"\n🏆 TABLE READINESS SCORES:")
    for table_name, data in results['detailed_results'].items():
        if 'ml_readiness' in data:
            ml_ready = data['ml_readiness']
            score = ml_ready['total_score']
            level = ml_ready['readiness_level'].upper()
            rows = data['basic_stats'].get('total_rows', 0)
            symbols = data['basic_stats'].get('unique_symbols', 'N/A')
            
            status_emoji = "🟢" if level in ['EXCELLENT', 'GOOD'] else "🟡" if level == 'FAIR' else "🔴"
            print(f"   {status_emoji} {table_name:<25} | Score: {score:3d}/100 | Level: {level:<9} | Records: {rows:>8,} | Symbols: {symbols}")
        else:
            print(f"   ❌ {table_name:<25} | ERROR: {data.get('error', 'Unknown')}")
    
    print(f"\n⚠️ KEY RECOMMENDATIONS:")
    if summary['recommendations']:
        for i, rec in enumerate(summary['recommendations'][:10], 1):  # Show top 10
            print(f"   {i}. {rec}")
    else:
        print("   🎉 All tables are in excellent condition!")
    
    print(f"\n📅 Analysis completed at: {results['analysis_timestamp']}")
    print("="*80)
    
    return results


if __name__ == "__main__":
    main()