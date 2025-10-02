#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def analyze_data_gaps():
    """Analyze specific data gaps and opportunities for improvement"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 COMPREHENSIVE DATA GAP ANALYSIS")
        print("=" * 60)
        
        # 1. OHLC Data Gaps Analysis
        print("\n=== OHLC DATA GAPS ===")
        
        # Check OHLC population by symbol
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total_records,
                SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) as has_ohlc,
                ROUND(SUM(CASE WHEN open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as ohlc_percentage
            FROM ml_features_materialized
            GROUP BY symbol
            HAVING ohlc_percentage < 50
            ORDER BY total_records DESC
            LIMIT 10
        """)
        
        low_ohlc_symbols = cursor.fetchall()
        print(f"Symbols with <50% OHLC coverage ({len(low_ohlc_symbols)} found):")
        for row in low_ohlc_symbols:
            print(f"  {row[0]:8} {row[2]:>6,}/{row[1]:>6,} ({row[3]:>6.1f}%)")
        
        # 2. Volume Data Analysis
        print("\n=== VOLUME DATA GAPS ===")
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total,
                SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) as has_volume,
                ROUND(SUM(CASE WHEN volume_24h > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as vol_pct
            FROM ml_features_materialized
            GROUP BY symbol
            HAVING vol_pct < 80
            ORDER BY total DESC
            LIMIT 10
        """)
        
        low_volume_symbols = cursor.fetchall()
        print(f"Symbols with <80% volume data:")
        for row in low_volume_symbols:
            print(f"  {row[0]:8} {row[2]:>6,}/{row[1]:>6,} ({row[3]:>6.1f}%)")
        
        # 3. Technical Indicators Coverage
        print("\n=== TECHNICAL INDICATORS GAPS ===")
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN sma_7 IS NOT NULL THEN 1 ELSE 0 END) as sma_7_count,
                SUM(CASE WHEN sma_30 IS NOT NULL THEN 1 ELSE 0 END) as sma_30_count,
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as rsi_count,
                SUM(CASE WHEN bb_upper IS NOT NULL THEN 1 ELSE 0 END) as bb_count,
                COUNT(*) as total
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        tech_indicators = cursor.fetchone()
        total = tech_indicators[4]
        print(f"Technical indicators coverage (last 7 days):")
        print(f"  SMA-7:  {tech_indicators[0]:>7,}/{total:,} ({tech_indicators[0]/total*100:.1f}%)")
        print(f"  SMA-30: {tech_indicators[1]:>7,}/{total:,} ({tech_indicators[1]/total*100:.1f}%)")
        print(f"  RSI-14: {tech_indicators[2]:>7,}/{total:,} ({tech_indicators[2]/total*100:.1f}%)")
        print(f"  BB:     {tech_indicators[3]:>7,}/{total:,} ({tech_indicators[3]/total*100:.1f}%)")
        
        # 4. Sentiment Data Gaps
        print("\n=== SENTIMENT DATA GAPS ===")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN crypto_sentiment_count > 0 THEN 1 ELSE 0 END) as has_crypto_sentiment,
                SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as has_sentiment_score
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        sentiment_data = cursor.fetchone()
        total = sentiment_data[0]
        print(f"Sentiment data coverage (last 7 days):")
        print(f"  Crypto sentiment: {sentiment_data[1]:>7,}/{total:,} ({sentiment_data[1]/total*100:.1f}%)")
        print(f"  Sentiment scores: {sentiment_data[2]:>7,}/{total:,} ({sentiment_data[2]/total*100:.1f}%)")
        
        # 5. Macro Indicators Consistency
        print("\n=== MACRO INDICATORS ANALYSIS ===")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN dxy IS NOT NULL THEN 1 ELSE 0 END) as has_dxy,
                SUM(CASE WHEN vix IS NOT NULL THEN 1 ELSE 0 END) as has_vix,
                SUM(CASE WHEN spx IS NOT NULL THEN 1 ELSE 0 END) as has_spx,
                SUM(CASE WHEN tnx IS NOT NULL THEN 1 ELSE 0 END) as has_tnx
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        macro_data = cursor.fetchone()
        total = macro_data[0]
        print(f"Macro indicators coverage (last 7 days):")
        print(f"  DXY: {macro_data[1]:>7,}/{total:,} ({macro_data[1]/total*100:.1f}%)")
        print(f"  VIX: {macro_data[2]:>7,}/{total:,} ({macro_data[2]/total*100:.1f}%)")
        print(f"  SPX: {macro_data[3]:>7,}/{total:,} ({macro_data[3]/total*100:.1f}%)")
        print(f"  TNX: {macro_data[4]:>7,}/{total:,} ({macro_data[4]/total*100:.1f}%)")
        
        # 6. Recent Data Freshness
        print("\n=== DATA FRESHNESS ANALYSIS ===")
        cursor.execute("""
            SELECT 
                symbol,
                MAX(timestamp) as latest_data,
                TIMESTAMPDIFF(HOUR, MAX(timestamp), NOW()) as hours_old
            FROM ml_features_materialized
            GROUP BY symbol
            HAVING hours_old > 24
            ORDER BY hours_old DESC
            LIMIT 10
        """)
        
        stale_data = cursor.fetchall()
        if stale_data:
            print(f"Symbols with stale data (>24h old):")
            for row in stale_data:
                print(f"  {row[0]:8} {row[1]} ({row[2]} hours old)")
        else:
            print("✅ All symbols have fresh data (<24h old)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing data gaps: {e}")
        return False


def suggest_improvements():
    """Suggest specific improvements based on gap analysis"""
    print("\n" + "=" * 60)
    print("🚀 IMPROVEMENT RECOMMENDATIONS")
    print("=" * 60)
    
    improvements = [
        {
            "priority": "HIGH",
            "area": "OHLC Data Backfill",
            "issue": "Some symbols still have <50% OHLC coverage",
            "solution": "Run targeted OHLC backfill for low-coverage symbols",
            "script": "backfill_missing_ohlc.py"
        },
        {
            "priority": "HIGH", 
            "area": "Volume Data Enhancement",
            "issue": "Volume data gaps in some symbols",
            "solution": "Enhance volume collection from multiple exchanges",
            "script": "enhance_volume_collection.py"
        },
        {
            "priority": "MEDIUM",
            "area": "Technical Indicators",
            "issue": "Technical indicators calculated real-time, coverage depends on data",
            "solution": "Improve underlying price data quality for better indicators",
            "script": "enhance_technical_indicators.py"
        },
        {
            "priority": "MEDIUM",
            "area": "Sentiment Data",
            "issue": "Sentiment data comes in batches, some gaps expected",
            "solution": "Increase sentiment collection frequency",
            "script": "enhance_sentiment_collection.py"
        },
        {
            "priority": "LOW",
            "area": "Macro Indicators",
            "issue": "Recently updated but could be more frequent",
            "solution": "Automate daily macro data updates",
            "script": "automate_macro_updates.py"
        }
    ]
    
    for i, improvement in enumerate(improvements, 1):
        priority_color = "🔴" if improvement["priority"] == "HIGH" else "🟡" if improvement["priority"] == "MEDIUM" else "🟢"
        print(f"\n{i}. {priority_color} {improvement['area']} [{improvement['priority']}]")
        print(f"   Issue: {improvement['issue']}")
        print(f"   Solution: {improvement['solution']}")
        print(f"   Implementation: {improvement['script']}")
    
    return improvements


def main():
    """Main function to analyze gaps and suggest improvements"""
    logger.info("Starting comprehensive data gap analysis...")
    
    if analyze_data_gaps():
        improvements = suggest_improvements()
        
        print(f"\n" + "=" * 60)
        print("✅ ANALYSIS COMPLETED")
        print(f"Found {len(improvements)} improvement opportunities")
        print("Priority: Implement HIGH priority items first")
        print("=" * 60)
        
        return True
    else:
        print("❌ Analysis failed")
        return False


if __name__ == "__main__":
    main()