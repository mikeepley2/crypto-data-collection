#!/usr/bin/env python3

import mysql.connector
from datetime import datetime

def main():
    print("=== VOLUME DATA COLLECTION ANALYSIS ===")
    print("Deep dive into volume data limitations and opportunities\n")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # 1. CURRENT VOLUME DATA SOURCES
        print("\n" + "="*50)
        print("1. CURRENT VOLUME DATA SOURCES ANALYSIS")
        print("="*50)
        
        # Check volume fields in price_data
        cursor.execute("DESCRIBE price_data")
        price_columns = [col[0] for col in cursor.fetchall()]
        volume_columns = [col for col in price_columns if 'volume' in col.lower()]
        
        print(f"📊 PRICE_DATA TABLE:")
        print(f"   Total columns: {len(price_columns)}")
        print(f"   Volume-related columns: {volume_columns}")
        
        # Check volume data population
        for col in volume_columns:
            cursor.execute(f"SELECT COUNT(*) FROM price_data WHERE {col} IS NOT NULL")
            populated = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM price_data")
            total = cursor.fetchone()[0]
            percentage = populated / total * 100 if total > 0 else 0
            
            print(f"   {col}: {populated:,}/{total:,} ({percentage:.1f}%)")
        
        # Check exchange coverage for volume data
        print(f"\n📈 EXCHANGE COVERAGE:")
        cursor.execute("SELECT exchange, COUNT(*) as records FROM price_data WHERE exchange IS NOT NULL GROUP BY exchange ORDER BY records DESC")
        exchanges = cursor.fetchall()
        
        total_with_exchange = sum(count for _, count in exchanges)
        cursor.execute("SELECT COUNT(*) FROM price_data")
        total_records = cursor.fetchone()[0]
        
        print(f"   Total records with exchange data: {total_with_exchange:,}/{total_records:,}")
        print(f"   Exchanges found:")
        for exchange, count in exchanges:
            percentage = count / total_with_exchange * 100 if total_with_exchange > 0 else 0
            print(f"     {exchange}: {count:,} records ({percentage:.1f}%)")
        
        # 2. VOLUME DATA IN ML FEATURES
        print("\n" + "="*50)
        print("2. VOLUME DATA IN ML FEATURES")
        print("="*50)
        
        cursor.execute("DESCRIBE ml_features_materialized")
        ml_columns = [col[0] for col in cursor.fetchall()]
        ml_volume_fields = [col for col in ml_columns if 'volume' in col.lower()]
        
        print(f"📊 ML FEATURES VOLUME FIELDS:")
        print(f"   Volume-related fields: {len(ml_volume_fields)}")
        
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_symbols = cursor.fetchone()[0]
        
        populated_volume_fields = 0
        for field in ml_volume_fields:
            cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {field} IS NOT NULL")
            populated = cursor.fetchone()[0]
            percentage = populated / total_symbols * 100 if total_symbols > 0 else 0
            status = "✅" if populated > 0 else "❌"
            
            print(f"   {status} {field}: {populated}/{total_symbols} ({percentage:.1f}%)")
            if populated > 0:
                populated_volume_fields += 1
        
        volume_coverage = populated_volume_fields / len(ml_volume_fields) * 100 if ml_volume_fields else 0
        print(f"\n🎯 VOLUME CATEGORY COVERAGE: {populated_volume_fields}/{len(ml_volume_fields)} ({volume_coverage:.1f}%)")
        
        # 3. VOLUME DATA FRESHNESS
        print("\n" + "="*50)
        print("3. VOLUME DATA FRESHNESS ANALYSIS")
        print("="*50)
        
        # Check latest volume data
        volume_tables = ['price_data', 'ohlc_data']
        for table in volume_tables:
            try:
                cursor.execute(f"SELECT MAX(timestamp) FROM {table}")
                latest = cursor.fetchone()[0]
                if latest:
                    age = datetime.now() - latest
                    status = "🟢" if age.total_seconds() < 3600 else "🟡" if age.total_seconds() < 86400 else "🔴"
                    print(f"   {status} {table}: Latest {latest}, Age: {age}")
                else:
                    print(f"   ❓ {table}: No timestamp data")
            except Exception as e:
                print(f"   ❌ {table}: Error - {e}")
        
        # 4. VOLUME DATA QUALITY ISSUES
        print("\n" + "="*50)
        print("4. VOLUME DATA QUALITY ISSUES")
        print("="*50)
        
        issues = []
        
        # Check for missing volume data
        cursor.execute("SELECT COUNT(*) FROM price_data WHERE volume_usd_24h IS NULL OR volume_usd_24h = 0")
        missing_volume = cursor.fetchone()[0]
        if missing_volume > 0:
            issues.append(f"Missing/zero volume data: {missing_volume:,} records")
        
        # Check exchange coverage gaps
        if len(exchanges) < 5:
            issues.append(f"Limited exchange coverage: Only {len(exchanges)} exchanges")
        
        # Check for volume spikes or anomalies
        cursor.execute("""
            SELECT symbol, MAX(volume_usd_24h) as max_vol, MIN(volume_usd_24h) as min_vol, AVG(volume_usd_24h) as avg_vol
            FROM price_data 
            WHERE volume_usd_24h IS NOT NULL AND volume_usd_24h > 0
            GROUP BY symbol 
            HAVING MAX(volume_usd_24h) > AVG(volume_usd_24h) * 100
            LIMIT 5
        """)
        
        anomalies = cursor.fetchall()
        if anomalies:
            issues.append(f"Volume anomalies detected: {len(anomalies)} symbols with 100x+ spikes")
        
        print(f"🚨 IDENTIFIED ISSUES:")
        for issue in issues:
            print(f"   ❌ {issue}")
        
        if not issues:
            print(f"   ✅ No major quality issues detected")
        
        # 5. EXPANSION OPPORTUNITIES
        print("\n" + "="*50)
        print("5. VOLUME DATA EXPANSION OPPORTUNITIES")
        print("="*50)
        
        opportunities = [
            "📈 Additional Exchanges: Kraken, Gemini, KuCoin, Gate.io",
            "🔄 DEX Integration: Uniswap, SushiSwap, PancakeSwap volumes",
            "📊 Volume Indicators: VWAP, Volume Profile, On-Balance Volume",
            "⏱️ Intraday Volume: Hourly volume breakdowns",
            "💹 Derivatives Volume: Futures and perpetual contract volumes",
            "🌐 Cross-Chain Volume: Multi-blockchain volume aggregation"
        ]
        
        print(f"💡 EXPANSION OPPORTUNITIES:")
        for opp in opportunities:
            print(f"   {opp}")
        
        # 6. RECOMMENDATIONS
        print("\n" + "="*50)
        print("6. VOLUME DATA IMPROVEMENT RECOMMENDATIONS")
        print("="*50)
        
        recommendations = [
            "1. Fix onchain_volume_24h integration in materialized updater",
            "2. Add Kraken API for additional volume data source", 
            "3. Implement DEX volume aggregation (CoinGecko DEX endpoints)",
            "4. Add volume-based technical indicators (VWAP, OBV)",
            "5. Create volume anomaly detection and filtering",
            "6. Implement real-time volume monitoring"
        ]
        
        print(f"🎯 PRIORITY RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   {rec}")
        
        cursor.close()
        connection.close()
        
        print(f"\n🏁 VOLUME DATA ANALYSIS COMPLETE")
        print(f"Next: Onchain Integration Optimization")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()