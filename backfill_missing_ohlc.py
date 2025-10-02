#!/usr/bin/env python3

import mysql.connector
import logging
from datetime import datetime, timedelta

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


def identify_ohlc_gaps():
    """Identify symbols and date ranges with missing OHLC data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 IDENTIFYING OHLC DATA GAPS")
        print("=" * 50)
        
        # Find symbols with low OHLC coverage that have OHLC data available
        cursor.execute("""
            SELECT 
                ml.symbol,
                COUNT(*) as ml_records,
                SUM(CASE WHEN ml.open_price IS NOT NULL THEN 1 ELSE 0 END) as has_ohlc,
                COUNT(DISTINCT ohlc.symbol) as has_ohlc_source,
                ROUND(SUM(CASE WHEN ml.open_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as ohlc_percentage
            FROM ml_features_materialized ml
            LEFT JOIN ohlc_data ohlc ON ml.symbol = ohlc.symbol
            GROUP BY ml.symbol
            HAVING ohlc_percentage < 70 AND has_ohlc_source > 0
            ORDER BY ml_records DESC, ohlc_percentage ASC
            LIMIT 20
        """)
        
        gap_symbols = cursor.fetchall()
        
        print(f"Found {len(gap_symbols)} symbols with OHLC gaps that can be filled:")
        print("Symbol   ML Records  OHLC Data  Available  Coverage")
        print("-" * 50)
        
        target_symbols = []
        for row in gap_symbols:
            symbol = row[0]
            ml_records = row[1]
            has_ohlc = row[2]
            has_source = row[3]
            percentage = row[4]
            
            print(f"{symbol:8} {ml_records:>10,} {has_ohlc:>9,} {has_source:>9} {percentage:>7.1f}%")
            
            if has_source > 0 and percentage < 60:  # Has source data but low coverage
                target_symbols.append(symbol)
        
        cursor.close()
        conn.close()
        return target_symbols
        
    except Exception as e:
        logger.error(f"Error identifying OHLC gaps: {e}")
        return []


def backfill_symbol_ohlc(symbol):
    """Backfill OHLC data for a specific symbol"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"Backfilling OHLC data for {symbol}")
        
        # Update ML features with available OHLC data using a JOIN
        update_query = """
            UPDATE ml_features_materialized ml
            INNER JOIN (
                SELECT 
                    symbol,
                    timestamp,
                    open,
                    high, 
                    low,
                    close,
                    volume,
                    ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp DESC) as rn
                FROM ohlc_data 
                WHERE symbol = %s
            ) ohlc ON ml.symbol = ohlc.symbol 
                  AND ml.timestamp = ohlc.timestamp 
                  AND ohlc.rn = 1
            SET 
                ml.open_price = ohlc.open,
                ml.high_price = ohlc.high,
                ml.low_price = ohlc.low,
                ml.close_price = ohlc.close,
                ml.ohlc_volume = ohlc.volume,
                ml.updated_at = NOW()
            WHERE ml.symbol = %s 
              AND (ml.open_price IS NULL OR ml.close_price IS NULL)
        """
        
        cursor.execute(update_query, (symbol, symbol))
        updated_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Updated {updated_count} records for {symbol}")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error backfilling OHLC for {symbol}: {e}")
        return 0


def improve_volume_data():
    """Improve volume data by copying from OHLC where missing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Improving volume data coverage")
        
        # Update volume data where missing but OHLC volume is available
        update_query = """
            UPDATE ml_features_materialized ml
            INNER JOIN (
                SELECT 
                    symbol,
                    timestamp,
                    volume,
                    ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp DESC) as rn
                FROM ohlc_data 
                WHERE volume > 0
            ) ohlc ON ml.symbol = ohlc.symbol 
                  AND ml.timestamp = ohlc.timestamp 
                  AND ohlc.rn = 1
            SET 
                ml.volume_24h = COALESCE(ml.volume_24h, ohlc.volume),
                ml.ohlc_volume = COALESCE(ml.ohlc_volume, ohlc.volume),
                ml.updated_at = NOW()
            WHERE (ml.volume_24h IS NULL OR ml.volume_24h = 0)
              AND ohlc.volume > 0
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Updated volume data for {updated_count} records")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error improving volume data: {e}")
        return 0


def enhance_recent_data():
    """Focus on enhancing data for the most recent time periods"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Enhancing recent data coverage")
        
        # Update recent records with any available OHLC data
        update_query = """
            UPDATE ml_features_materialized ml
            INNER JOIN (
                SELECT 
                    symbol,
                    timestamp,
                    open,
                    high,
                    low, 
                    close,
                    volume,
                    ROW_NUMBER() OVER (PARTITION BY symbol, timestamp ORDER BY timestamp DESC) as rn
                FROM ohlc_data 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ) ohlc ON ml.symbol = ohlc.symbol 
                  AND ml.timestamp = ohlc.timestamp 
                  AND ohlc.rn = 1
            SET 
                ml.open_price = COALESCE(ml.open_price, ohlc.open),
                ml.high_price = COALESCE(ml.high_price, ohlc.high),
                ml.low_price = COALESCE(ml.low_price, ohlc.low),
                ml.close_price = COALESCE(ml.close_price, ohlc.close),
                ml.ohlc_volume = COALESCE(ml.ohlc_volume, ohlc.volume),
                ml.updated_at = NOW()
            WHERE ml.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
              AND (ml.open_price IS NULL OR ml.close_price IS NULL)
        """
        
        cursor.execute(update_query)
        updated_count = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Enhanced {updated_count} recent records")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error enhancing recent data: {e}")
        return 0


def main():
    """Main function to run OHLC backfill improvements"""
    logger.info("Starting OHLC data improvement process...")
    
    print("🚀 OHLC DATA IMPROVEMENT PROCESS")
    print("=" * 60)
    
    total_improvements = 0
    
    # Step 1: Identify gaps
    gap_symbols = identify_ohlc_gaps()
    
    if gap_symbols:
        print(f"\n📊 Targeting {len(gap_symbols)} symbols for improvement:")
        
        # Step 2: Backfill top priority symbols (limit to avoid overload)
        priority_symbols = gap_symbols[:10]  # Top 10 most critical
        
        for symbol in priority_symbols:
            print(f"\n🔄 Processing {symbol}...")
            improvements = backfill_symbol_ohlc(symbol)
            total_improvements += improvements
    
    # Step 3: Improve volume data
    print(f"\n🔄 Improving volume data coverage...")
    volume_improvements = improve_volume_data()
    total_improvements += volume_improvements
    
    # Step 4: Focus on recent data
    print(f"\n🔄 Enhancing recent data (last 7 days)...")
    recent_improvements = enhance_recent_data()
    total_improvements += recent_improvements
    
    print(f"\n" + "=" * 60)
    print(f"✅ IMPROVEMENT COMPLETED")
    print(f"Total records improved: {total_improvements:,}")
    print(f"Symbols processed: {len(gap_symbols) if gap_symbols else 0}")
    print("=" * 60)
    
    return total_improvements > 0


if __name__ == "__main__":
    main()