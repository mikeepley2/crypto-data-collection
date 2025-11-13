#!/usr/bin/env python3
"""
Comprehensive Data Quality Assessment and Backfill Planning
This tool analyzes data quality across all tables and identifies backfill needs.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.database_config import get_db_connection
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityAssessment:
    """Comprehensive data quality assessment and backfill planning"""
    
    def __init__(self):
        self.connection = get_db_connection()
        self.cursor = self.connection.cursor(dictionary=True)
        self.assessment_date = datetime.now()
        self.target_days = 30  # Assess last 30 days
        
    def get_table_list(self) -> List[str]:
        """Get list of all data collection tables"""
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'crypto_prices' 
        AND table_name IN (
            'crypto_news', 'crypto_onchain_data', 'ohlc_data', 
            'technical_indicators', 'macro_indicators', 'sentiment_data'
        )
        ORDER BY table_name
        """
        
        self.cursor.execute(tables_query)
        tables = [row['table_name'] for row in self.cursor.fetchall()]
        logger.info(f"📋 Found {len(tables)} data collection tables: {tables}")
        return tables
    
    def assess_table_completeness(self, table_name: str) -> Dict:
        """Assess completeness for a specific table"""
        logger.info(f"🔍 Assessing {table_name}...")
        
        # Get table structure
        self.cursor.execute(f"DESCRIBE {table_name}")
        columns = [row['Field'] for row in self.cursor.fetchall()]
        
        # Determine date column
        date_columns = ['created_at', 'timestamp_iso', 'date', 'indicator_date', 'timestamp']
        date_column = None
        for col in date_columns:
            if col in columns:
                date_column = col
                break
        
        if not date_column:
            logger.warning(f"⚠️  No date column found for {table_name}")
            return {'table': table_name, 'status': 'no_date_column'}
        
        # Calculate date range for assessment
        end_date = self.assessment_date
        start_date = end_date - timedelta(days=self.target_days)
        
        # Get total records in date range
        total_query = f"""
        SELECT COUNT(*) as total_records,
               MIN({date_column}) as earliest_date,
               MAX({date_column}) as latest_date,
               COUNT(DISTINCT DATE({date_column})) as distinct_days
        FROM {table_name}
        WHERE {date_column} >= %s AND {date_column} <= %s
        """
        
        self.cursor.execute(total_query, (start_date, end_date))
        basic_stats = self.cursor.fetchone()
        
        # Check for gaps in data
        gap_query = f"""
        WITH RECURSIVE date_range AS (
            SELECT DATE(%s) as check_date
            UNION ALL
            SELECT DATE_ADD(check_date, INTERVAL 1 DAY)
            FROM date_range
            WHERE check_date < DATE(%s)
        ),
        daily_counts AS (
            SELECT DATE({date_column}) as data_date, COUNT(*) as daily_count
            FROM {table_name}
            WHERE {date_column} >= %s AND {date_column} <= %s
            GROUP BY DATE({date_column})
        )
        SELECT dr.check_date,
               COALESCE(dc.daily_count, 0) as record_count
        FROM date_range dr
        LEFT JOIN daily_counts dc ON dr.check_date = dc.data_date
        ORDER BY dr.check_date
        """
        
        self.cursor.execute(gap_query, (start_date, end_date, start_date, end_date))
        daily_data = self.cursor.fetchall()
        
        # Analyze gaps
        missing_days = [row['check_date'] for row in daily_data if row['record_count'] == 0]
        low_volume_days = [row['check_date'] for row in daily_data if 0 < row['record_count'] < 5]
        
        # Column completeness analysis
        column_stats = {}
        for column in columns:
            if column != date_column:
                col_query = f"""
                SELECT COUNT(*) as total,
                       COUNT({column}) as non_null,
                       COUNT(*) - COUNT({column}) as null_count
                FROM {table_name}
                WHERE {date_column} >= %s AND {date_column} <= %s
                """
                self.cursor.execute(col_query, (start_date, end_date))
                col_result = self.cursor.fetchone()
                
                if col_result['total'] > 0:
                    completeness = (col_result['non_null'] / col_result['total']) * 100
                    column_stats[column] = {
                        'completeness': completeness,
                        'null_count': col_result['null_count'],
                        'total': col_result['total']
                    }
        
        return {
            'table': table_name,
            'date_column': date_column,
            'total_records': basic_stats['total_records'],
            'date_range': f"{basic_stats['earliest_date']} to {basic_stats['latest_date']}",
            'distinct_days': basic_stats['distinct_days'],
            'expected_days': self.target_days,
            'missing_days': len(missing_days),
            'missing_days_list': missing_days[:10],  # First 10 missing days
            'low_volume_days': len(low_volume_days),
            'column_stats': column_stats,
            'data_quality_score': self._calculate_quality_score(
                basic_stats['distinct_days'], self.target_days, 
                len(missing_days), column_stats
            )
        }
    
    def _calculate_quality_score(self, distinct_days: int, expected_days: int, 
                               missing_days: int, column_stats: Dict) -> float:
        """Calculate overall data quality score (0-100)"""
        # Temporal coverage score (0-40 points)
        temporal_score = min(40, (distinct_days / expected_days) * 40)
        
        # Completeness score (0-40 points)
        avg_completeness = sum(col['completeness'] for col in column_stats.values()) / len(column_stats) if column_stats else 0
        completeness_score = (avg_completeness / 100) * 40
        
        # Consistency score (0-20 points) - penalize missing days
        consistency_score = max(0, 20 - (missing_days * 2))
        
        return round(temporal_score + completeness_score + consistency_score, 1)
    
    def generate_backfill_plan(self, assessments: List[Dict]) -> Dict:
        """Generate comprehensive backfill plan"""
        backfill_plan = {
            'urgent': [],      # < 50% quality score
            'medium': [],      # 50-80% quality score
            'maintenance': [], # 80-95% quality score
            'good': []         # > 95% quality score
        }
        
        for assessment in assessments:
            table = assessment['table']
            score = assessment['data_quality_score']
            missing_days = assessment['missing_days']
            
            priority_info = {
                'table': table,
                'score': score,
                'missing_days': missing_days,
                'actions_needed': []
            }
            
            # Determine actions needed
            if missing_days > 10:
                priority_info['actions_needed'].append('Comprehensive historical backfill')
            elif missing_days > 3:
                priority_info['actions_needed'].append('Recent gap backfill')
            
            # Check column completeness issues
            for col, stats in assessment.get('column_stats', {}).items():
                if stats['completeness'] < 90:
                    priority_info['actions_needed'].append(f'Fix {col} completeness ({stats["completeness"]:.1f}%)')
            
            # Categorize by priority
            if score < 50:
                backfill_plan['urgent'].append(priority_info)
            elif score < 80:
                backfill_plan['medium'].append(priority_info)
            elif score < 95:
                backfill_plan['maintenance'].append(priority_info)
            else:
                backfill_plan['good'].append(priority_info)
        
        return backfill_plan
    
    def run_assessment(self) -> Tuple[List[Dict], Dict]:
        """Run complete data quality assessment"""
        logger.info("🚀 Starting comprehensive data quality assessment...")
        
        tables = self.get_table_list()
        assessments = []
        
        for table in tables:
            try:
                assessment = self.assess_table_completeness(table)
                assessments.append(assessment)
            except Exception as e:
                logger.error(f"❌ Failed to assess {table}: {e}")
                assessments.append({
                    'table': table,
                    'status': 'error',
                    'error': str(e),
                    'data_quality_score': 0
                })
        
        # Generate backfill plan
        backfill_plan = self.generate_backfill_plan(assessments)
        
        return assessments, backfill_plan
    
    def print_assessment_report(self, assessments: List[Dict], backfill_plan: Dict):
        """Print comprehensive assessment report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DATA QUALITY ASSESSMENT REPORT")
        print("=" * 80)
        print(f"Assessment Date: {self.assessment_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Assessment Period: Last {self.target_days} days")
        print()
        
        # Summary statistics
        total_tables = len(assessments)
        avg_score = sum(a.get('data_quality_score', 0) for a in assessments) / total_tables if total_tables > 0 else 0
        
        print(f"📋 SUMMARY")
        print(f"  Total Tables Assessed: {total_tables}")
        print(f"  Average Quality Score: {avg_score:.1f}/100")
        print()
        
        # Individual table details
        print(f"📈 TABLE DETAILS")
        print("-" * 80)
        
        for assessment in sorted(assessments, key=lambda x: x.get('data_quality_score', 0), reverse=True):
            table = assessment['table']
            score = assessment.get('data_quality_score', 0)
            
            if assessment.get('status') == 'error':
                print(f"❌ {table:<20} ERROR: {assessment.get('error', 'Unknown error')}")
                continue
            
            missing = assessment.get('missing_days', 0)
            records = assessment.get('total_records', 0)
            
            status_emoji = "🟢" if score >= 95 else "🟡" if score >= 80 else "🟠" if score >= 50 else "🔴"
            
            print(f"{status_emoji} {table:<20} Score: {score:>5.1f} | Records: {records:>6,} | Missing Days: {missing:>2}")
            
            # Show significant issues
            if missing > 0:
                missing_dates = assessment.get('missing_days_list', [])[:3]
                print(f"    Missing: {', '.join(str(d) for d in missing_dates)}{'...' if missing > 3 else ''}")
            
            # Show column issues
            for col, stats in assessment.get('column_stats', {}).items():
                if stats['completeness'] < 90:
                    print(f"    {col}: {stats['completeness']:.1f}% complete")
        
        print()
        
        # Backfill plan
        print(f"🔧 BACKFILL PRIORITY PLAN")
        print("-" * 80)
        
        for priority, items in backfill_plan.items():
            if items:
                priority_emoji = {"urgent": "🚨", "medium": "⚠️", "maintenance": "🔧", "good": "✅"}
                print(f"{priority_emoji[priority]} {priority.upper()} ({len(items)} tables):")
                
                for item in items:
                    print(f"  • {item['table']} (Score: {item['score']:.1f})")
                    for action in item['actions_needed']:
                        print(f"    - {action}")
                print()
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.connection.close()

if __name__ == "__main__":
    assessment = DataQualityAssessment()
    
    try:
        assessments, backfill_plan = assessment.run_assessment()
        assessment.print_assessment_report(assessments, backfill_plan)
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data_quality_assessment_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            import sys
            from io import StringIO
            
            # Capture print output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            assessment.print_assessment_report(assessments, backfill_plan)
            report_content = sys.stdout.getvalue()
            
            sys.stdout = old_stdout
            f.write(report_content)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
    finally:
        assessment.close()