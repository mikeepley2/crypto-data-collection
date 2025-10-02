#!/usr/bin/env python3

import mysql.connector
import os
from datetime import datetime, timedelta

def main():
    print("=== MACRO DATA EXPANSION ANALYSIS ===\n")
    
    try:
        # Database connection using actual environment (run from local machine)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'crypto_user'),
            password=os.getenv('DB_PASSWORD', 'cryptoP@ss123!'),
            database=os.getenv('DB_NAME', 'crypto_prices')
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # Check current macro indicators table
        print("🔍 Analyzing macro_indicators table...")
        cursor.execute("DESCRIBE macro_indicators")
        columns = [col[0] for col in cursor.fetchall()]
        print(f"   Available columns: {len(columns)}")
        for col in columns:
            print(f"      {col}")
        
        # Check data availability and freshness
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT indicator_type) as unique_indicators,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                AVG(CASE WHEN value IS NOT NULL THEN 1 ELSE 0 END) * 100 as value_fill_rate
            FROM macro_indicators
        """)
        
        result = cursor.fetchone()
        if result:
            total, unique_indicators, earliest, latest, fill_rate = result
            print(f"\n📊 MACRO_INDICATORS TABLE STATUS:")
            print(f"   Total records: {total:,}")
            print(f"   Unique indicator types: {unique_indicators}")
            print(f"   Date range: {earliest} to {latest}")
            print(f"   Value fill rate: {fill_rate:.1f}%")
        
        # Check what indicators we have
        cursor.execute("""
            SELECT 
                indicator_type,
                COUNT(*) as record_count,
                MIN(date) as first_date,
                MAX(date) as last_date,
                AVG(value) as avg_value,
                COUNT(CASE WHEN value IS NOT NULL THEN 1 END) as non_null_count
            FROM macro_indicators
            GROUP BY indicator_type
            ORDER BY record_count DESC
        """)
        
        indicators = cursor.fetchall()
        print(f"\n📋 AVAILABLE MACRO INDICATORS ({len(indicators)} types):")
        for indicator_type, count, first_date, last_date, avg_val, non_null in indicators:
            print(f"   {indicator_type}: {count:,} records ({first_date} to {last_date})")
            print(f"      Avg: {avg_val:.4f}, Non-null: {non_null:,}")
        
        # Check current ML features macro field population
        print(f"\n🔍 Checking current macro field population in ml_features_materialized...")
        
        # Get all columns that might be macro-related
        cursor.execute("DESCRIBE ml_features_materialized")
        all_columns = [col[0] for col in cursor.fetchall()]
        
        # Identify potential macro fields
        macro_keywords = ['vix', 'dxy', 'yield', 'fed', 'treasury', 'bond', 'rate', 'gdp', 'cpi', 'pmi', 'unemployment', 
                         'tnx', 'dgs', 'fedfunds', 'unrate', 'cpiaucsl', 'gdpc1', 'effr', 'dexjpus', 'dtwexbgs']
        macro_fields = []
        for col in all_columns:
            if any(keyword in col.lower() for keyword in macro_keywords):
                macro_fields.append(col)
        
        print(f"   Potential macro fields found: {len(macro_fields)}")
        for field in macro_fields:
            print(f"      {field}")
        
        # Check population of these fields
        if macro_fields:
            field_checks = []
            for field in macro_fields:
                field_checks.append(f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count")
            
            query = f"""
                SELECT 
                    COUNT(*) as total_symbols,
                    {', '.join(field_checks)}
                FROM ml_features_materialized
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                total_symbols = result[0]
                print(f"\n📊 MACRO FIELD POPULATION (out of {total_symbols} symbols):")
                
                populated_fields = 0
                for i, field in enumerate(macro_fields):
                    count = result[i + 1]  # +1 because first field is total_symbols
                    percentage = count / total_symbols * 100 if total_symbols > 0 else 0
                    status = "✅" if count > 0 else "❌"
                    print(f"   {status} {field}: {count} ({percentage:.1f}%)")
                    if count > 0:
                        populated_fields += 1
                
                print(f"\n🎯 MACRO CATEGORY STATUS:")
                print(f"   Fields populated: {populated_fields}/{len(macro_fields)}")
                print(f"   Category completion: {populated_fields/len(macro_fields)*100:.1f}%")
        
        # Sample BTC macro values
        cursor.execute(f"""
            SELECT {', '.join(macro_fields[:10])} 
            FROM ml_features_materialized 
            WHERE symbol = 'BTC'
        """)
        
        btc_result = cursor.fetchone()
        if btc_result and macro_fields:
            print(f"\n📋 BTC SAMPLE MACRO VALUES:")
            for i, field in enumerate(macro_fields[:10]):
                value = btc_result[i] if i < len(btc_result) else None
                print(f"   {field}: {value}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 Suggestion: Run from Kubernetes pod with database access")

if __name__ == "__main__":
    main()