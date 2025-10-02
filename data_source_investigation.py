#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta
from collections import defaultdict

def main():
    print("=== COMPREHENSIVE DATA SOURCE INVESTIGATION ===")
    print("Phase 2: Data Source Analysis and Expansion Opportunities")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='news_collector', 
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected")
        
        cursor = connection.cursor()
        
        # 1. COMPLETE DATA INVENTORY
        print("\n" + "="*60)
        print("1. COMPLETE DATA SOURCE INVENTORY")
        print("="*60)
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        data_sources = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"DESCRIBE {table}")
            columns = len(cursor.fetchall())
            
            # Try to get latest timestamp if available
            latest = None
            try:
                cursor.execute(f"SELECT MAX(timestamp) FROM {table}")
                result = cursor.fetchone()
                if result and result[0]:
                    latest = result[0]
            except:
                try:
                    cursor.execute(f"SELECT MAX(date) FROM {table}")
                    result = cursor.fetchone()
                    if result and result[0]:
                        latest = result[0]
                except:
                    pass
            
            data_sources[table] = {
                'records': count,
                'columns': columns,
                'latest': latest
            }
        
        # Categorize data sources
        price_tables = [t for t in tables if 'price' in t.lower()]
        sentiment_tables = [t for t in tables if 'sentiment' in t.lower()]
        technical_tables = [t for t in tables if 'technical' in t.lower()]
        macro_tables = [t for t in tables if 'macro' in t.lower()]
        onchain_tables = [t for t in tables if 'onchain' in t.lower()]
        ohlc_tables = [t for t in tables if 'ohlc' in t.lower()]
        volume_tables = [t for t in tables if 'volume' in t.lower()]
        other_tables = [t for t in tables if t not in price_tables + sentiment_tables + 
                       technical_tables + macro_tables + onchain_tables + ohlc_tables + volume_tables]
        
        categories = {
            'Price Data': price_tables,
            'Sentiment Data': sentiment_tables,
            'Technical Indicators': technical_tables,
            'Macro Economic': macro_tables,
            'Onchain Data': onchain_tables,
            'OHLC Data': ohlc_tables,
            'Volume Data': volume_tables,
            'Other': other_tables
        }
        
        total_records = 0
        for category, table_list in categories.items():
            if not table_list:
                continue
                
            print(f"\n📊 {category.upper()}:")
            category_records = 0
            for table in table_list:
                info = data_sources[table]
                category_records += info['records']
                freshness = ""
                if info['latest']:
                    try:
                        age = datetime.now() - info['latest']
                        if age.days == 0:
                            freshness = f"(fresh)"
                        elif age.days <= 1:
                            freshness = f"(1 day old)"
                        elif age.days <= 7:
                            freshness = f"({age.days} days old)"
                        else:
                            freshness = f"(stale: {age.days} days)"
                    except:
                        freshness = f"(latest: {info['latest']})"
                
                print(f"   {table}: {info['records']:,} records, {info['columns']} columns {freshness}")
            
            print(f"   CATEGORY TOTAL: {category_records:,} records")
            total_records += category_records
        
        print(f"\n🎯 TOTAL DATA ECOSYSTEM: {total_records:,} records across {len(tables)} tables")
        
        # 2. ML FEATURES POPULATION ANALYSIS
        print("\n" + "="*60)
        print("2. ML FEATURES POPULATION ANALYSIS")
        print("="*60)
        
        cursor.execute("DESCRIBE ml_features_materialized")
        ml_columns = [col[0] for col in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
        total_symbols = cursor.fetchone()[0]
        
        print(f"ML Features table: {total_symbols} symbols, {len(ml_columns)} total fields")
        
        # Analyze population by category
        field_categories = {
            'Price': ['price_usd', 'price_change_24h', 'price_change_7d', 'price_change_30d'],
            'Volume': ['volume_usd_24h', 'volume_change_24h', 'volume_weighted_price'],
            'Market': ['market_cap_usd', 'market_cap_rank', 'market_dominance'],
            'Technical': [f for f in ml_columns if 'tech_' in f or 'rsi' in f or 'macd' in f or 'sma' in f or 'ema' in f],
            'Sentiment': [f for f in ml_columns if 'sentiment' in f],
            'Macro': [f for f in ml_columns if 'macro_' in f],
            'Onchain': [f for f in ml_columns if 'onchain_' in f or 'transaction_count' in f],
            'OHLC': [f for f in ml_columns if f in ['open', 'high', 'low', 'close']],
            'Volatility': [f for f in ml_columns if 'volatility' in f or 'std' in f]
        }
        
        category_stats = {}
        for category, fields in field_categories.items():
            if not fields:
                continue
                
            populated_fields = 0
            total_population = 0
            
            for field in fields:
                if field in ml_columns:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM ml_features_materialized WHERE {field} IS NOT NULL")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            populated_fields += 1
                            total_population += count
                    except:
                        continue
            
            category_stats[category] = {
                'total_fields': len(fields),
                'populated_fields': populated_fields,
                'avg_population': total_population / len(fields) if fields else 0,
                'coverage': populated_fields / len(fields) * 100 if fields else 0
            }
        
        print(f"\n📈 ML FEATURE CATEGORIES ANALYSIS:")
        for category, stats in category_stats.items():
            coverage = stats['coverage']
            status = "✅" if coverage > 75 else "🔧" if coverage > 25 else "❌"
            print(f"   {status} {category}: {stats['populated_fields']}/{stats['total_fields']} fields ({coverage:.1f}%)")
        
        # 3. DATA FRESHNESS ANALYSIS
        print("\n" + "="*60)
        print("3. DATA FRESHNESS & QUALITY ANALYSIS")  
        print("="*60)
        
        # Check key tables for freshness
        key_tables = ['price_data', 'technical_indicators', 'sentiment_aggregated_daily', 
                     'macro_indicators', 'crypto_onchain_data_enhanced']
        
        for table in key_tables:
            if table in tables:
                try:
                    cursor.execute(f"SELECT MAX(timestamp) as latest, MIN(timestamp) as earliest, COUNT(*) as total FROM {table}")
                    result = cursor.fetchone()
                    if result:
                        latest, earliest, total = result
                        if latest and earliest:
                            span = latest - earliest
                            age = datetime.now() - latest
                            
                            status = "🟢" if age.total_seconds() < 3600 else "🟡" if age.total_seconds() < 86400 else "🔴"
                            print(f"   {status} {table}: {total:,} records")
                            print(f"      Span: {earliest} to {latest} ({span.days} days)")
                            print(f"      Freshness: {age}")
                except Exception as e:
                    print(f"   ❓ {table}: Could not analyze - {e}")
        
        # 4. IDENTIFY GAPS AND OPPORTUNITIES
        print("\n" + "="*60)
        print("4. DATA GAPS & EXPANSION OPPORTUNITIES")
        print("="*60)
        
        gaps = []
        
        # Volume data gaps
        if not volume_tables:
            gaps.append("❌ No dedicated volume tables found")
        
        # Exchange coverage
        cursor.execute("SELECT DISTINCT exchange FROM price_data WHERE exchange IS NOT NULL")
        exchanges = [row[0] for row in cursor.fetchall()]
        if len(exchanges) < 5:
            gaps.append(f"🔧 Limited exchange coverage: {len(exchanges)} exchanges")
        
        # DeFi data
        defi_tables = [t for t in tables if 'defi' in t.lower() or 'liquidity' in t.lower() or 'yield' in t.lower()]
        if not defi_tables:
            gaps.append("❌ No DeFi/liquidity data sources")
        
        # Derivatives data
        derivatives_tables = [t for t in tables if 'futures' in t.lower() or 'options' in t.lower() or 'perpetual' in t.lower()]
        if not derivatives_tables:
            gaps.append("❌ No derivatives market data")
        
        # News/social data beyond sentiment
        news_tables = [t for t in tables if 'news' in t.lower() or 'social' in t.lower()]
        if not news_tables:
            gaps.append("❌ No raw news/social data (only processed sentiment)")
        
        print("🎯 IDENTIFIED GAPS:")
        for gap in gaps:
            print(f"   {gap}")
        
        # 5. EXPANSION RECOMMENDATIONS
        print(f"\n💡 EXPANSION RECOMMENDATIONS:")
        print(f"   1. Exchange Coverage: Add Kraken, Gemini, KuCoin APIs")
        print(f"   2. DeFi Integration: Uniswap, Compound, Aave TVL/APY data")
        print(f"   3. Derivatives Data: CME futures, perpetual funding rates")
        print(f"   4. Social Expansion: Twitter sentiment, Reddit analysis")
        print(f"   5. News Integration: CoinDesk, Cointelegraph RSS feeds")
        print(f"   6. Alternative Data: GitHub commits, developer activity")
        
        cursor.close()
        connection.close()
        
        print(f"\n🏁 DATA SOURCE INVESTIGATION COMPLETE")
        print(f"Next: Focus on Volume Data Collection Analysis")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()