#!/usr/bin/env python3
"""
Comprehensive Data Quality Analysis
Analyzes all data sources for gaps, quality issues, and prioritizes fixes
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from shared.database_config import get_db_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityAnalyzer:
    def __init__(self):
        self.conn = get_db_connection()
        if not self.conn:
            raise Exception("Failed to connect to database")
        self.cursor = self.conn.cursor(dictionary=True)
        self.results = {}
        self.priority_issues = []
        
    def analyze_all_sources(self):
        """Run comprehensive analysis across all data sources"""
        logger.info("🔍 Starting comprehensive data quality analysis...")
        
        # Core data sources
        self.analyze_price_data()
        self.analyze_news_data()
        self.analyze_sentiment_data()
        self.analyze_onchain_data()
        self.analyze_technical_indicators()
        self.analyze_macro_indicators()
        
        # Data relationships and consistency
        self.analyze_data_consistency()
        self.analyze_recent_coverage()
        
        # Generate priority report
        self.generate_priority_report()
        
        logger.info("✅ Data quality analysis complete")
        
    def analyze_price_data(self):
        """Analyze OHLC price data quality"""
        logger.info("📊 Analyzing price data...")
        
        # Check OHLC data coverage and quality
        queries = {
            'ohlc_total_records': "SELECT COUNT(*) as count FROM crypto_ohlc_data",
            'ohlc_date_range': """
                SELECT MIN(date) as earliest, MAX(date) as latest, 
                       COUNT(DISTINCT date) as unique_dates,
                       COUNT(DISTINCT symbol) as unique_symbols
                FROM crypto_ohlc_data
            """,
            'ohlc_null_issues': """
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
                    SUM(CASE WHEN high IS NULL THEN 1 ELSE 0 END) as null_high,
                    SUM(CASE WHEN low IS NULL THEN 1 ELSE 0 END) as null_low,
                    SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
                    SUM(CASE WHEN volume IS NULL THEN 1 ELSE 0 END) as null_volume
                FROM crypto_ohlc_data
            """,
            'ohlc_recent_coverage': """
                SELECT DATE(date) as date, COUNT(*) as symbols_count
                FROM crypto_ohlc_data 
                WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                GROUP BY DATE(date)
                ORDER BY date DESC
            """,
            'ohlc_zero_volume': """
                SELECT COUNT(*) as zero_volume_count,
                       COUNT(DISTINCT symbol) as symbols_affected
                FROM crypto_ohlc_data 
                WHERE volume = 0 AND date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """
        }
        
        price_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                price_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                price_results[key] = []
        
        self.results['price_data'] = price_results
        
        # Check for critical issues
        if price_results['ohlc_null_issues']:
            nulls = price_results['ohlc_null_issues'][0]
            total = nulls['total_records']
            if any(nulls[f'null_{col}'] > 0 for col in ['open', 'high', 'low', 'close']):
                self.priority_issues.append({
                    'category': 'price_data',
                    'severity': 'HIGH',
                    'issue': 'NULL values in OHLC data',
                    'details': f"Found NULL values in price columns out of {total:,} records"
                })
    
    def analyze_news_data(self):
        """Analyze news data quality"""
        logger.info("📰 Analyzing news data...")
        
        queries = {
            'news_total': "SELECT COUNT(*) as count FROM crypto_news",
            'news_date_range': """
                SELECT MIN(published_date) as earliest, MAX(published_date) as latest,
                       COUNT(DISTINCT DATE(published_date)) as unique_dates
                FROM crypto_news
            """,
            'news_recent_coverage': """
                SELECT DATE(published_date) as date, COUNT(*) as articles_count
                FROM crypto_news 
                WHERE published_date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                GROUP BY DATE(published_date)
                ORDER BY date DESC
            """,
            'news_sources': """
                SELECT source, COUNT(*) as article_count
                FROM crypto_news
                WHERE published_date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
                GROUP BY source
                ORDER BY article_count DESC
            """,
            'news_null_content': """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as null_title,
                    SUM(CASE WHEN content IS NULL OR content = '' THEN 1 ELSE 0 END) as null_content,
                    SUM(CASE WHEN url IS NULL OR url = '' THEN 1 ELSE 0 END) as null_url
                FROM crypto_news
                WHERE published_date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """
        }
        
        news_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                news_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                news_results[key] = []
        
        self.results['news_data'] = news_results
        
        # Check for news gap issues
        if news_results['news_recent_coverage']:
            recent_days = len(news_results['news_recent_coverage'])
            if recent_days < 5:  # Less than 5 days of recent data
                self.priority_issues.append({
                    'category': 'news_data',
                    'severity': 'MEDIUM',
                    'issue': 'Insufficient recent news coverage',
                    'details': f"Only {recent_days} days of news data in last 7 days"
                })
    
    def analyze_sentiment_data(self):
        """Analyze sentiment data quality"""
        logger.info("😊 Analyzing sentiment data...")
        
        queries = {
            'sentiment_total': """
                SELECT 
                    (SELECT COUNT(*) FROM crypto_news_sentiment) as news_sentiment,
                    (SELECT COUNT(*) FROM stock_sentiment) as stock_sentiment
            """,
            'sentiment_date_range': """
                SELECT 
                    'news_sentiment' as type,
                    MIN(timestamp) as earliest, 
                    MAX(timestamp) as latest
                FROM crypto_news_sentiment
                UNION ALL
                SELECT 
                    'stock_sentiment' as type,
                    MIN(collection_date) as earliest,
                    MAX(collection_date) as latest
                FROM stock_sentiment
            """,
            'sentiment_scores_distribution': """
                SELECT 
                    ROUND(sentiment_score, 1) as score_range,
                    COUNT(*) as count
                FROM crypto_news_sentiment
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
                GROUP BY ROUND(sentiment_score, 1)
                ORDER BY score_range
            """,
            'sentiment_null_scores': """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN sentiment_score IS NULL THEN 1 ELSE 0 END) as null_scores,
                    SUM(CASE WHEN sentiment_score < -1 OR sentiment_score > 1 THEN 1 ELSE 0 END) as invalid_scores
                FROM crypto_news_sentiment
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """
        }
        
        sentiment_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                sentiment_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                sentiment_results[key] = []
        
        self.results['sentiment_data'] = sentiment_results
        
        # Check sentiment data issues
        if sentiment_results['sentiment_null_scores']:
            nulls = sentiment_results['sentiment_null_scores'][0]
            if nulls['null_scores'] > 0:
                self.priority_issues.append({
                    'category': 'sentiment_data',
                    'severity': 'MEDIUM',
                    'issue': 'NULL sentiment scores found',
                    'details': f"{nulls['null_scores']} NULL scores out of {nulls['total']} records"
                })
    
    def analyze_onchain_data(self):
        """Analyze onchain data quality"""
        logger.info("⛓️ Analyzing onchain data...")
        
        queries = {
            'onchain_total': "SELECT COUNT(*) as count FROM crypto_onchain_data",
            'onchain_date_range': """
                SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest,
                       COUNT(DISTINCT DATE(timestamp)) as unique_dates,
                       COUNT(DISTINCT coin_symbol) as unique_symbols
                FROM crypto_onchain_data
            """,
            'onchain_recent_coverage': """
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as records_count,
                       COUNT(DISTINCT coin_symbol) as symbols_count
                FROM crypto_onchain_data 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """,
            'onchain_data_completeness': """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN active_addresses_24h IS NOT NULL THEN 1 ELSE 0 END) as has_addresses,
                    SUM(CASE WHEN transaction_count_24h IS NOT NULL THEN 1 ELSE 0 END) as has_transactions,
                    SUM(CASE WHEN price_volatility_7d IS NOT NULL THEN 1 ELSE 0 END) as has_volatility
                FROM crypto_onchain_data
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """,
            'onchain_gap_check': """
                SELECT 
                    TIMESTAMPDIFF(HOUR, MAX(timestamp), NOW()) as hours_since_last_update
                FROM crypto_onchain_data
            """
        }
        
        onchain_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                onchain_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                onchain_results[key] = []
        
        self.results['onchain_data'] = onchain_results
        
        # Check for onchain gaps
        if onchain_results['onchain_gap_check']:
            gap_hours = onchain_results['onchain_gap_check'][0]['hours_since_last_update']
            if gap_hours and gap_hours > 12:
                self.priority_issues.append({
                    'category': 'onchain_data',
                    'severity': 'HIGH' if gap_hours > 24 else 'MEDIUM',
                    'issue': 'Onchain data gap detected',
                    'details': f"{gap_hours:.1f} hours since last update"
                })
    
    def analyze_technical_indicators(self):
        """Analyze technical indicators quality"""
        logger.info("📈 Analyzing technical indicators...")
        
        queries = {
            'bollinger_bands': """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN bb_upper IS NOT NULL THEN 1 ELSE 0 END) as has_upper,
                       SUM(CASE WHEN bb_middle IS NOT NULL THEN 1 ELSE 0 END) as has_middle,
                       SUM(CASE WHEN bb_lower IS NOT NULL THEN 1 ELSE 0 END) as has_lower
                FROM bollinger_bands
                WHERE date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """,
            'rsi_data': """
                SELECT COUNT(*) as total,
                       MIN(rsi_value) as min_rsi,
                       MAX(rsi_value) as max_rsi,
                       AVG(rsi_value) as avg_rsi
                FROM rsi_data
                WHERE date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """,
            'macd_data': """
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) as has_macd,
                       SUM(CASE WHEN signal_line IS NOT NULL THEN 1 ELSE 0 END) as has_signal,
                       SUM(CASE WHEN histogram IS NOT NULL THEN 1 ELSE 0 END) as has_histogram
                FROM macd_data
                WHERE date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """,
            'technical_coverage': """
                SELECT 
                    'bollinger' as indicator,
                    COUNT(DISTINCT symbol) as symbols_covered,
                    MAX(date) as latest_date
                FROM bollinger_bands
                WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                UNION ALL
                SELECT 
                    'rsi' as indicator,
                    COUNT(DISTINCT symbol) as symbols_covered,
                    MAX(date) as latest_date
                FROM rsi_data
                WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                UNION ALL
                SELECT 
                    'macd' as indicator,
                    COUNT(DISTINCT symbol) as symbols_covered,
                    MAX(date) as latest_date
                FROM macd_data
                WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
            """
        }
        
        tech_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                tech_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                tech_results[key] = []
        
        self.results['technical_indicators'] = tech_results
    
    def analyze_macro_indicators(self):
        """Analyze macro economic indicators"""
        logger.info("🌍 Analyzing macro indicators...")
        
        queries = {
            'macro_total': "SELECT COUNT(*) as count FROM macro_indicators",
            'macro_indicators_list': """
                SELECT indicator_name, 
                       COUNT(*) as records,
                       MIN(date) as earliest,
                       MAX(date) as latest
                FROM macro_indicators
                GROUP BY indicator_name
                ORDER BY records DESC
            """,
            'macro_recent': """
                SELECT indicator_name,
                       COUNT(*) as recent_records
                FROM macro_indicators
                WHERE date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
                GROUP BY indicator_name
                ORDER BY recent_records DESC
            """,
            'macro_null_values': """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as null_values
                FROM macro_indicators
                WHERE date >= DATE_SUB(NOW(), INTERVAL 30 DAYS)
            """
        }
        
        macro_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                macro_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                macro_results[key] = []
        
        self.results['macro_indicators'] = macro_results
    
    def analyze_data_consistency(self):
        """Check data consistency across sources"""
        logger.info("🔍 Analyzing data consistency...")
        
        queries = {
            'symbol_consistency': """
                SELECT 
                    'ohlc' as source, COUNT(DISTINCT symbol) as unique_symbols
                FROM crypto_ohlc_data
                WHERE date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                UNION ALL
                SELECT 
                    'onchain' as source, COUNT(DISTINCT coin_symbol) as unique_symbols
                FROM crypto_onchain_data
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
            """,
            'date_alignment': """
                SELECT 
                    DATE(o.date) as date,
                    COUNT(DISTINCT o.symbol) as ohlc_symbols,
                    COUNT(DISTINCT oc.coin_symbol) as onchain_symbols
                FROM crypto_ohlc_data o
                LEFT JOIN crypto_onchain_data oc ON DATE(o.date) = DATE(oc.timestamp)
                WHERE o.date >= DATE_SUB(NOW(), INTERVAL 7 DAYS)
                GROUP BY DATE(o.date)
                ORDER BY date DESC
            """
        }
        
        consistency_results = {}
        for key, query in queries.items():
            try:
                self.cursor.execute(query)
                consistency_results[key] = self.cursor.fetchall()
            except Exception as e:
                logger.error(f"Error in {key}: {e}")
                consistency_results[key] = []
        
        self.results['data_consistency'] = consistency_results
    
    def analyze_recent_coverage(self):
        """Analyze recent data coverage across all sources"""
        logger.info("📅 Analyzing recent coverage...")
        
        now = datetime.now()
        recent_dates = [(now - timedelta(days=i)).date() for i in range(7)]
        
        coverage_by_date = {}
        for date in recent_dates:
            coverage_by_date[str(date)] = {}
            
            # Check each data source for this date
            sources = {
                'ohlc': f"SELECT COUNT(DISTINCT symbol) as count FROM crypto_ohlc_data WHERE DATE(date) = '{date}'",
                'news': f"SELECT COUNT(*) as count FROM crypto_news WHERE DATE(published_date) = '{date}'",
                'onchain': f"SELECT COUNT(DISTINCT coin_symbol) as count FROM crypto_onchain_data WHERE DATE(timestamp) = '{date}'",
                'sentiment': f"SELECT COUNT(*) as count FROM crypto_news_sentiment WHERE DATE(timestamp) = '{date}'"
            }
            
            for source, query in sources.items():
                try:
                    self.cursor.execute(query)
                    result = self.cursor.fetchone()
                    coverage_by_date[str(date)][source] = result['count'] if result else 0
                except Exception as e:
                    logger.error(f"Error checking {source} for {date}: {e}")
                    coverage_by_date[str(date)][source] = 0
        
        self.results['recent_coverage'] = coverage_by_date
    
    def generate_priority_report(self):
        """Generate prioritized action report"""
        logger.info("📋 Generating priority report...")
        
        # Calculate overall scores
        scores = self._calculate_data_scores()
        
        # Sort issues by severity
        high_priority = [issue for issue in self.priority_issues if issue['severity'] == 'HIGH']
        medium_priority = [issue for issue in self.priority_issues if issue['severity'] == 'MEDIUM']
        low_priority = [issue for issue in self.priority_issues if issue['severity'] == 'LOW']
        
        self.results['priority_summary'] = {
            'overall_scores': scores,
            'high_priority_issues': high_priority,
            'medium_priority_issues': medium_priority,
            'low_priority_issues': low_priority,
            'total_issues': len(self.priority_issues)
        }
    
    def _calculate_data_scores(self):
        """Calculate data quality scores for each source"""
        scores = {}
        
        # Price data score
        if 'price_data' in self.results and self.results['price_data']['ohlc_null_issues']:
            nulls = self.results['price_data']['ohlc_null_issues'][0]
            total = nulls['total_records']
            null_count = sum(nulls[f'null_{col}'] for col in ['open', 'high', 'low', 'close'])
            scores['price_data'] = max(0, 100 - (null_count / total * 100)) if total > 0 else 0
        
        # News data score  
        if 'news_data' in self.results and self.results['news_data']['news_recent_coverage']:
            recent_days = len(self.results['news_data']['news_recent_coverage'])
            scores['news_data'] = min(100, (recent_days / 7) * 100)
        
        # Onchain data score
        if 'onchain_data' in self.results and self.results['onchain_data']['onchain_gap_check']:
            gap_hours = self.results['onchain_data']['onchain_gap_check'][0]['hours_since_last_update']
            if gap_hours is not None:
                scores['onchain_data'] = max(0, 100 - min(gap_hours * 2, 100))
            else:
                scores['onchain_data'] = 0
        
        return scores
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "="*80)
        print("🔍 COMPREHENSIVE DATA QUALITY ANALYSIS REPORT")
        print("="*80)
        
        # Overall scores
        if 'priority_summary' in self.results and 'overall_scores' in self.results['priority_summary']:
            print("\n📊 DATA QUALITY SCORES:")
            for source, score in self.results['priority_summary']['overall_scores'].items():
                status = "🟢" if score > 80 else "🟡" if score > 60 else "🔴"
                print(f"   {status} {source.replace('_', ' ').title()}: {score:.1f}/100")
        
        # High priority issues
        if self.priority_issues:
            print(f"\n🚨 PRIORITY ISSUES FOUND ({len(self.priority_issues)} total):")
            
            high_issues = [i for i in self.priority_issues if i['severity'] == 'HIGH']
            if high_issues:
                print("\n   🔴 HIGH PRIORITY:")
                for issue in high_issues:
                    print(f"      • {issue['issue']} ({issue['category']})")
                    print(f"        {issue['details']}")
            
            medium_issues = [i for i in self.priority_issues if i['severity'] == 'MEDIUM']
            if medium_issues:
                print("\n   🟡 MEDIUM PRIORITY:")
                for issue in medium_issues:
                    print(f"      • {issue['issue']} ({issue['category']})")
                    print(f"        {issue['details']}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND!")
        
        # Recent coverage summary
        if 'recent_coverage' in self.results:
            print("\n📅 RECENT DATA COVERAGE (Last 7 days):")
            for date, sources in list(self.results['recent_coverage'].items())[:3]:  # Show last 3 days
                print(f"\n   📆 {date}:")
                for source, count in sources.items():
                    status = "✅" if count > 0 else "❌"
                    print(f"      {status} {source.upper()}: {count:,} records")
        
        # Data volumes
        print("\n📈 DATA VOLUMES:")
        if 'price_data' in self.results and self.results['price_data']['ohlc_total_records']:
            count = self.results['price_data']['ohlc_total_records'][0]['count']
            print(f"   💰 OHLC Data: {count:,} records")
        
        if 'news_data' in self.results and self.results['news_data']['news_total']:
            count = self.results['news_data']['news_total'][0]['count']
            print(f"   📰 News Articles: {count:,} records")
        
        if 'onchain_data' in self.results and self.results['onchain_data']['onchain_total']:
            count = self.results['onchain_data']['onchain_total'][0]['count']
            print(f"   ⛓️  Onchain Data: {count:,} records")
        
        print("\n" + "="*80)
    
    def save_detailed_report(self, filename='data_quality_report.json'):
        """Save detailed results to JSON file"""
        # Convert datetime objects to strings for JSON serialization
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=json_serial)
        
        logger.info(f"📄 Detailed report saved to {filename}")
    
    def cleanup(self):
        """Cleanup database connections"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def main():
    """Main analysis function"""
    analyzer = None
    try:
        analyzer = DataQualityAnalyzer()
        analyzer.analyze_all_sources()
        analyzer.print_summary()
        analyzer.save_detailed_report()
        
        # Return priority focus areas
        priority_issues = analyzer.priority_issues
        if priority_issues:
            print("\n🎯 RECOMMENDED FOCUS AREAS:")
            high_priority = [i for i in priority_issues if i['severity'] == 'HIGH']
            if high_priority:
                print("   1. Address HIGH priority issues first:")
                for i, issue in enumerate(high_priority, 1):
                    print(f"      {i}. {issue['issue']} ({issue['category']})")
            
            medium_priority = [i for i in priority_issues if i['severity'] == 'MEDIUM']
            if medium_priority:
                print("   2. Then address MEDIUM priority issues:")
                for i, issue in enumerate(medium_priority, 1):
                    print(f"      {i}. {issue['issue']} ({issue['category']})")
        else:
            print("\n🎉 All data sources are in good condition!")
            print("   Focus on: Regular monitoring and maintenance")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
    finally:
        if analyzer:
            analyzer.cleanup()

if __name__ == "__main__":
    main()