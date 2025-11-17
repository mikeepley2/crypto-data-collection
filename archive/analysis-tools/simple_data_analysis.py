#!/usr/bin/env python3
"""
Simple Data Quality Analysis for ML Readiness
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
        # Check if table exists
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not cursor.fetchone():
            print(f"   ❌ Table {table_name} does not exist")
            return {"status": "missing", "score": 0}
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        # Get date range (try common timestamp columns)
        date_cols = ['timestamp', 'created_at', 'date', 'time']
        min_date = max_date = None
        
        for date_col in date_cols:
            try:
                cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table_name} WHERE {date_col} IS NOT NULL")
                result = cursor.fetchone()
                if result and result[0]:
                    min_date, max_date = result
                    break
            except:
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
            if isinstance(max_date, str):
                try:
                    max_date = datetime.strptime(max_date, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        max_date = datetime.strptime(max_date, '%Y-%m-%d')
                    except:
                        max_date = None
            
            if max_date and (datetime.now() - max_date).days < 7:
                score += 10
        
        print(f"   ✅ {table_name}: {status.upper()} (Score: {score}/100)")
        print(f"      - Rows: {row_count:,}")
        print(f"      - Columns: {len(columns)}")
        if min_date and max_date:
            print(f"      - Date Range: {min_date} to {max_date}")
        
        return {
            "status": status,
            "score": score,
            "rows": row_count,
            "columns": len(columns),
            "min_date": str(min_date) if min_date else None,
            "max_date": str(max_date) if max_date else None
        }
        
    except Exception as e:
        print(f"   ❌ {table_name}: Error - {str(e)}")
        return {"status": "error", "score": 0, "error": str(e)}

def main():
    """Main analysis function."""
    print("🚀 Starting Simple Data Quality Analysis for ML Readiness")
    print("=" * 60)
    
    # Target tables for our 7 collectors
    tables = [
        'technical_indicators',    # Enhanced Technical Calculator
        'macro_indicators',        # Enhanced Macro Collector
        'crypto_prices',          # Enhanced Crypto Prices
        'crypto_news',            # News Collector
        'ohlc_data',              # OHLC Collector
        'crypto_onchain_data',    # Onchain Collector
        'price_data_real'         # Enhanced Sentiment
    ]
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return
    
    cursor = conn.cursor()
    results = {}
    
    for table in tables:
        try:
            results[table] = analyze_table(cursor, table)
        except Exception as e:
            print(f"❌ Failed to analyze {table}: {e}")
            results[table] = {"status": "error", "score": 0, "error": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ML READINESS SUMMARY")
    print("=" * 60)
    
    total_score = 0
    valid_tables = 0
    
    for table, result in results.items():
        if result['score'] > 0:
            total_score += result['score']
            valid_tables += 1
            print(f"✅ {table}: {result['score']}/100 ({result['status']})")
        else:
            print(f"❌ {table}: {result['score']}/100 ({result.get('status', 'unknown')})")
    
    overall_score = total_score / len(tables) if tables else 0
    
    print(f"\n🎯 OVERALL ML READINESS: {overall_score:.1f}/100")
    print(f"📈 Valid Tables: {valid_tables}/{len(tables)}")
    
    if overall_score >= 70:
        print("🟢 EXCELLENT: Ready for ML/Signal Generation")
    elif overall_score >= 50:
        print("🟡 GOOD: Suitable for ML with some improvements")
    elif overall_score >= 30:
        print("🟠 MODERATE: Needs improvement before ML")
    else:
        print("🔴 POOR: Significant data quality issues")
    
    conn.close()
    print("\n✨ Analysis complete!")

if __name__ == "__main__":
    main()