#!/usr/bin/env python3

import mysql.connector
import sys

def main():
    print("=== DATABASE CLEANUP - REMOVING LOW-QUALITY TABLES ===")
    print("This will remove empty and low-quality tables while keeping essential data sources")
    
    # Connect to database
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='news_collector',
            password='99Rules!',
            database='crypto_prices'
        )
        print("✅ Database connected successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
        
    cursor = connection.cursor()
    
    # Tables to remove - empty and low-quality tables identified
    tables_to_remove = [
        # Empty tables (0 records)
        'crypto_news_articles',
        'crypto_onchain_data_enhanced_backup', 
        'crypto_sentiment_news_old',
        'feature_quality_v2_old',
        'macro_economic_data_old',
        'market_movers_old',
        'market_regimes_v2_old',
        'model_performance_v2_old',
        'new_coin_listings_old',
        'onchain_metrics_old',
        'price_data_backup_structure',
        'price_summary_daily_old',
        'sentiment_scores_old',
        'sentiment_scoring_history_old',
        'sentiment_signals_old',
        'service_alerts_old',
        'signal_analytics_old',
        'social_media_posts',
        'social_platform_stats',
        'social_sentiment_analysis_old',
        'social_sentiment_metrics',
        'stock_market_news_data',
        'stock_market_sentiment_data',
        'trading_engine_v2_metrics_old',
        
        # Very low quality tables (< 100 records, redundant data)
        'global_market_data',  # 1 record
        'market_trends_summary',  # 1 record
        'sentiment_data',  # 12 records (superseded by advanced sentiment)
        'unified_sentiment_data'  # 12 records (superseded)
    ]
    
    # Tables to keep (essential data sources)
    essential_tables = [
        'price_data_real',  # 3.8M records - main price data
        'hourly_data',  # 3.3M records  
        'ml_features_materialized',  # 3.3M records - core ML features
        'ohlc_data',  # 188K records - OHLC candle data
        'technical_indicators',  # 121K records - technical analysis
        'real_time_sentiment_signals',  # 114K records - sentiment processing
        'crypto_onchain_data',  # 101K records - onchain metrics
        'sentiment_aggregation',  # 68K records - aggregated sentiment
        'macro_indicators',  # 49K records - economic indicators
        'price_data',  # 26K records - recent price data
        'trading_signals',  # 26K records - trading engine output
        'crypto_assets',  # 362 records - asset metadata
        'crypto_metadata',  # 34 records - crypto metadata
        'crypto_onchain_data_enhanced'  # 48 records - enhanced onchain (needs fixing but keep)
    ]
    
    print(f"\n📊 CLEANUP PLAN:")
    print(f"   Tables to remove: {len(tables_to_remove)}")
    print(f"   Essential tables to keep: {len(essential_tables)}")
    
    # Check current table status
    cursor.execute("SHOW TABLES")
    current_tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\n🔍 CURRENT STATE:")
    print(f"   Total tables: {len(current_tables)}")
    
    # Verify tables exist before removal
    tables_to_remove_verified = []
    for table in tables_to_remove:
        if table in current_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                tables_to_remove_verified.append((table, count))
                print(f"   ✓ {table}: {count} records (will remove)")
            except:
                print(f"   ⚠️ {table}: Error checking (will skip)")
        else:
            print(f"   ℹ️ {table}: Not found (already removed)")
    
    # Confirm cleanup
    if not tables_to_remove_verified:
        print("\n✅ No tables need to be removed")
        cursor.close()
        connection.close()
        return
        
    print(f"\n⚠️ ABOUT TO REMOVE {len(tables_to_remove_verified)} TABLES:")
    for table, count in tables_to_remove_verified:
        print(f"   • {table} ({count} records)")
    
    response = input("\nProceed with cleanup? (yes/no): ").lower().strip()
    if response != 'yes':
        print("❌ Cleanup cancelled")
        cursor.close()
        connection.close()
        return
    
    # Perform cleanup
    print(f"\n🧹 STARTING CLEANUP...")
    removed_count = 0
    total_records_removed = 0
    
    for table, count in tables_to_remove_verified:
        try:
            print(f"   Removing {table}...")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            removed_count += 1
            total_records_removed += count
            print(f"   ✅ Removed {table} ({count} records)")
        except Exception as e:
            print(f"   ❌ Failed to remove {table}: {e}")
    
    # Commit changes
    connection.commit()
    
    # Final status
    cursor.execute("SHOW TABLES")
    final_tables = [table[0] for table in cursor.fetchall()]
    
    print(f"\n🎯 CLEANUP COMPLETE:")
    print(f"   Tables removed: {removed_count}")
    print(f"   Records removed: {total_records_removed:,}")
    print(f"   Remaining tables: {len(final_tables)}")
    
    # Show remaining table stats
    print(f"\n📊 REMAINING TABLES (by size):")
    table_stats = []
    for table in final_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            table_stats.append((table, count))
        except:
            table_stats.append((table, 0))
    
    # Sort by record count
    table_stats.sort(key=lambda x: x[1], reverse=True)
    
    for table, count in table_stats[:20]:  # Show top 20
        if count > 1000:
            print(f"   {table}: {count:,} records")
        else:
            print(f"   {table}: {count} records")
    
    # Check for any potential issues
    print(f"\n🔍 QUALITY CHECK:")
    small_tables = [t for t, c in table_stats if 0 < c < 100]
    if small_tables:
        print(f"   ⚠️ Small tables remaining: {len(small_tables)}")
        for table in small_tables[:5]:
            print(f"      • {table}")
    else:
        print(f"   ✅ No small tables remaining")
    
    zero_tables = [t for t, c in table_stats if c == 0]
    if zero_tables:
        print(f"   ⚠️ Empty tables remaining: {len(zero_tables)}")
        for table in zero_tables[:5]:
            print(f"      • {table}")
    else:
        print(f"   ✅ No empty tables remaining")
    
    cursor.close()
    connection.close()
    
    print(f"\n🏁 DATABASE CLEANUP SUCCESSFUL")
    print(f"Removed {removed_count} low-quality tables, freed {total_records_removed:,} records")
    print(f"Database is now cleaner and more efficient!")

if __name__ == "__main__":
    main()