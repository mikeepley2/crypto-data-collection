#!/usr/bin/env python3
"""
Fixed Data Quality Analysis for ML Readiness
Now uses direct table access instead of problematic views
"""

import mysql.connector
from datetime import datetime, timedelta
import sys
import traceback

def get_db_connection():
    """Get database connection with proper settings."""
    try:
        return mysql.connector.connect(
            host='172.22.32.1',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices',
            charset='utf8mb4',
            sql_mode='',
            autocommit=True
        )
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def analyze_table(cursor, table_name):
    """Analyze a single table for ML readiness."""
    print(f"\n🔍 Analyzing {table_name}...")
    
    try:
        # Check if table exists and is not a view
        cursor.execute(f"SHOW FULL TABLES LIKE '{table_name}'")
        result = cursor.fetchone()
        if not result:
            print(f"   ❌ Table {table_name} does not exist")
            return {"status": "missing", "score": 0}
        
        table_type = result[1]
        if table_type == 'VIEW':
            print(f"   ⚠️ {table_name} is a VIEW - skipping")
            return {"status": "view_skipped", "score": 0}
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        # Get date range (try common timestamp columns)
        date_cols = ['timestamp', 'created_at', 'date', 'time', 'timestamp_iso', 'collection_date', 'indicator_date']
        min_date = max_date = date_col_used = None
        
        for date_col in date_cols:
            try:
                # Create fresh cursor for each query to avoid unread results
                fresh_cursor = cursor.connection.cursor()
                fresh_cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name} WHERE {date_col} IS NOT NULL LIMIT 1")
                result = fresh_cursor.fetchone()
                fresh_cursor.close()
                if result and result[0]:
                    min_date, max_date = result
                    date_col_used = date_col
                    break
            except Exception as e:
                continue
        
        # Calculate basic metrics
        if row_count == 0:
            score = 0
            status = "empty"
        elif row_count < 1000:
            score = 30
            status = "low_data"
        elif row_count < 10000:
            score = 60
            status = "moderate_data"
        else:
            score = 80
            status = "good_data"
        
        # Boost score for recent data
        if max_date:
            # Handle different date formats
            try:
                if isinstance(max_date, str):
                    try:
                        max_date = datetime.strptime(max_date, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            max_date = datetime.strptime(max_date, '%Y-%m-%d')
                        except:
                            max_date = None
                
                if max_date and isinstance(max_date, datetime):
                    days_old = (datetime.now() - max_date).days
                    if days_old < 1:
                        score += 15  # Very recent
                    elif days_old < 7:
                        score += 10  # Recent
                    elif days_old < 30:
                        score += 5   # Somewhat recent
            except:
                pass
        
        print(f"   ✅ {table_name}: {status.upper()} (Score: {score}/100)")
        print(f"      - Rows: {row_count:,}")
        print(f"      - Columns: {len(columns)}")
        if date_col_used and min_date and max_date:
            print(f"      - Date Range ({date_col_used}): {min_date} to {max_date}")
        
        return {
            "status": status,
            "score": score,
            "rows": row_count,
            "columns": len(columns),
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None,
            "date_column": date_col_used
        }
        
    except Exception as e:
        print(f"   ❌ {table_name}: Error - {str(e)}")
        return {"status": "error", "score": 0, "error": str(e)}

def main():
    """Main analysis function."""
    print("🚀 Starting Fixed Data Quality Analysis for ML Readiness")
    print("📋 Now using direct table access (no views)")
    print("=" * 60)
    
    # Updated table mapping - using underlying tables instead of views
    tables = {
        'technical_indicators': 'Enhanced Technical Calculator',
        'macro_indicators': 'Enhanced Macro Collector', 
        'price_data_real': 'Enhanced Crypto Prices (real table)', # Instead of crypto_prices view
        'crypto_news': 'News Collector',
        'ohlc_data': 'OHLC Collector',
        'crypto_onchain_data': 'Onchain Collector', # Instead of onchain_metrics view
        'ml_features_materialized': 'Enhanced Sentiment (materialized features)'
    }
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return
    
    # Test connection and close it - we'll create fresh connections per table
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()  # Consume the result
    cursor.close()
    conn.close()
    print("✅ Database connection verified")
    
    results = {}
    
    for table, collector in tables.items():
        try:
            print(f"\n📊 Collector: {collector}")
            # Create fresh connection for each table to avoid cursor issues
            table_conn = get_db_connection()
            if table_conn:
                table_cursor = table_conn.cursor()
                results[table] = analyze_table(table_cursor, table)
                table_cursor.close()
                table_conn.close()
            else:
                results[table] = {"status": "connection_error", "score": 0, "error": "Cannot connect"}
        except Exception as e:
            print(f"❌ Failed to analyze {table}: {e}")
            results[table] = {"status": "error", "score": 0, "error": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ML READINESS SUMMARY")
    print("=" * 60)
    
    total_score = 0
    valid_tables = 0
    excellent_tables = []
    good_tables = []
    moderate_tables = []
    poor_tables = []
    
    for table, result in results.items():
        score = result['score']
        if score >= 80:
            excellent_tables.append(f"{table} ({score})")
            total_score += score
            valid_tables += 1
        elif score >= 60:
            good_tables.append(f"{table} ({score})")
            total_score += score
            valid_tables += 1
        elif score >= 30:
            moderate_tables.append(f"{table} ({score})")
            total_score += score
            valid_tables += 1
        else:
            poor_tables.append(f"{table} ({score})")
    
    overall_score = total_score / len(tables) if tables else 0
    
    print(f"🟢 EXCELLENT (80-100): {len(excellent_tables)} tables")
    for table in excellent_tables:
        print(f"   ✅ {table}")
    
    print(f"\\n🟡 GOOD (60-79): {len(good_tables)} tables") 
    for table in good_tables:
        print(f"   ✅ {table}")
        
    print(f"\\n🟠 MODERATE (30-59): {len(moderate_tables)} tables")
    for table in moderate_tables:
        print(f"   ⚠️ {table}")
        
    print(f"\\n🔴 POOR (0-29): {len(poor_tables)} tables")
    for table in poor_tables:
        print(f"   ❌ {table}")
    
    print(f"\\n🎯 OVERALL ML READINESS: {overall_score:.1f}/100")
    print(f"📈 Valid Tables: {valid_tables}/{len(tables)}")
    
    if overall_score >= 70:
        print("🎉 EXCELLENT: Ready for ML/Signal Generation")
        print("💡 Recommendation: Begin feature engineering and model development")
    elif overall_score >= 50:
        print("✅ GOOD: Suitable for ML with some improvements")
        print("💡 Recommendation: Address moderate-scoring tables, then proceed")
    elif overall_score >= 30:
        print("⚠️ MODERATE: Needs improvement before ML")
        print("💡 Recommendation: Focus on data quality improvements first")
    else:
        print("🚨 POOR: Significant data quality issues")
        print("💡 Recommendation: Major data collection fixes needed")
    
    # Specific recommendations
    print(f"\\n🔧 NEXT STEPS:")
    if poor_tables:
        print(f"1. 🚨 CRITICAL: Fix {len(poor_tables)} failing tables")
    if moderate_tables:
        print(f"2. ⚠️ IMPROVE: Enhance {len(moderate_tables)} moderate tables")
    if excellent_tables or good_tables:
        print(f"3. 🚀 BUILD: Start ML features using {len(excellent_tables + good_tables)} ready tables")
    
    print("\n✨ Analysis complete!")

if __name__ == "__main__":
    main()