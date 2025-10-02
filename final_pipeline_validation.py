#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta

def validate_data_pipeline():
    """Final validation that the entire data pipeline is working"""
    
    try:
        conn = mysql.connector.connect(
            host='host.docker.internal',
            database='crypto_prices',
            user='news_collector',
            password='99Rules!'
        )
        cursor = conn.cursor()
        
        print("🔍 FINAL PIPELINE VALIDATION")
        print(f"⏰ Current time: {datetime.now()}")
        print("=" * 50)
        
        # 1. Check fresh price data collection
        cursor.execute("""
            SELECT COUNT(*) as count, MAX(timestamp) as latest 
            FROM price_data 
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        result = cursor.fetchone()
        fresh_count = result[0]
        latest_price = result[1]
        
        print(f"📊 PRICE COLLECTION:")
        print(f"   Fresh records (last hour): {fresh_count}")
        print(f"   Latest timestamp: {latest_price}")
        print(f"   Status: {'✅ EXCELLENT' if fresh_count > 100 else '⚠️ LOW' if fresh_count > 0 else '❌ STALE'}")
        print()
        
        # 2. Check materialized processing
        cursor.execute("""
            SELECT COUNT(*) as count, MAX(timestamp_iso) as latest, 
                   AVG(data_quality_score) as avg_quality
            FROM ml_features_materialized 
            WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        result = cursor.fetchone()
        processed_count = result[0] or 0
        latest_processed = result[1]
        avg_quality = result[2] or 0
        
        print(f"🧮 MATERIALIZED PROCESSING:")
        print(f"   Processed records (last hour): {processed_count}")
        print(f"   Latest processed: {latest_processed}")
        print(f"   Average quality score: {avg_quality:.2f}")
        
        # Calculate processing lag
        if latest_price and latest_processed:
            lag_minutes = (latest_price - latest_processed).total_seconds() / 60
            print(f"   Processing lag: {lag_minutes:.1f} minutes")
            status = '✅ REAL-TIME' if lag_minutes < 10 else '⚠️ LAGGED' if lag_minutes < 60 else '❌ STALE'
            print(f"   Status: {status}")
        else:
            print(f"   Status: ❌ NO DATA")
        print()
        
        # 3. Check symbol coverage
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) as symbols
            FROM ml_features_materialized 
            WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        symbol_count = cursor.fetchone()[0] or 0
        
        print(f"💰 SYMBOL COVERAGE:")
        print(f"   Unique symbols processed: {symbol_count}")
        print(f"   Status: {'✅ GOOD' if symbol_count > 50 else '⚠️ LIMITED' if symbol_count > 10 else '❌ POOR'}")
        print()
        
        # 4. Check technical indicators
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) * 100 as rsi_coverage,
                AVG(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) * 100 as macd_coverage,
                AVG(CASE WHEN vwap IS NOT NULL THEN 1 ELSE 0 END) * 100 as vwap_coverage
            FROM ml_features_materialized 
            WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        result = cursor.fetchone()
        if result and result[0] is not None:
            rsi_cov, macd_cov, vwap_cov = result
            print(f"📈 TECHNICAL INDICATORS:")
            print(f"   RSI-14 coverage: {rsi_cov:.1f}%")
            print(f"   MACD coverage: {macd_cov:.1f}%")
            print(f"   VWAP coverage: {vwap_cov:.1f}%")
            avg_tech_coverage = (rsi_cov + macd_cov + vwap_cov) / 3
            print(f"   Status: {'✅ EXCELLENT' if avg_tech_coverage > 80 else '⚠️ PARTIAL' if avg_tech_coverage > 50 else '❌ POOR'}")
        else:
            print(f"📈 TECHNICAL INDICATORS: ❌ NO DATA")
        print()
        
        # 5. Check macro indicators
        cursor.execute("""
            SELECT 
                AVG(CASE WHEN vix_index IS NOT NULL THEN 1 ELSE 0 END) * 100 as vix_coverage,
                AVG(CASE WHEN spx_price IS NOT NULL THEN 1 ELSE 0 END) * 100 as spx_coverage,
                AVG(CASE WHEN dxy_index IS NOT NULL THEN 1 ELSE 0 END) * 100 as dxy_coverage
            FROM ml_features_materialized 
            WHERE timestamp_iso > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        result = cursor.fetchone()
        if result and result[0] is not None:
            vix_cov, spx_cov, dxy_cov = result
            print(f"🌍 MACRO INDICATORS (FIXED!):")
            print(f"   VIX coverage: {vix_cov:.1f}%")
            print(f"   SPX coverage: {spx_cov:.1f}%") 
            print(f"   DXY coverage: {dxy_cov:.1f}%")
            avg_macro_coverage = (vix_cov + spx_cov + dxy_cov) / 3
            print(f"   Status: {'✅ EXCELLENT' if avg_macro_coverage > 80 else '⚠️ PARTIAL' if avg_macro_coverage > 50 else '❌ POOR'}")
        else:
            print(f"🌍 MACRO INDICATORS: ❌ NO DATA")
        print()
        
        # Overall assessment
        print("🎯 OVERALL ASSESSMENT:")
        issues = []
        if fresh_count < 100:
            issues.append("Low price collection")
        if processed_count < 100:
            issues.append("Low processing rate")
        if symbol_count < 50:
            issues.append("Limited symbol coverage")
            
        if not issues:
            print("   ✅ ALL SYSTEMS OPERATIONAL!")
            print("   🚀 Data pipeline running at full capacity")
        else:
            print(f"   ⚠️ Issues detected: {', '.join(issues)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    validate_data_pipeline()