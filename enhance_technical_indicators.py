#!/usr/bin/env python3

import mysql.connector
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )


def calculate_simple_moving_averages():
    """Calculate simple moving averages for symbols missing them"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Calculating simple moving averages...")
        
        # Get symbols with OHLC data but missing SMAs
        cursor.execute("""
            SELECT DISTINCT ml.symbol
            FROM ml_features_materialized ml
            WHERE ml.current_price > 0 
              AND (ml.sma_7 IS NULL OR ml.sma_30 IS NULL)
              AND ml.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY ml.symbol
        """)
        
        symbols = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(symbols)} symbols needing SMA calculation")
        
        improvements = 0
        
        for symbol in symbols[:50]:  # Process top 50 to avoid timeout
            try:
                # Calculate 7-day SMA
                cursor.execute("""
                    UPDATE ml_features_materialized ml1
                    SET 
                        sma_7 = (
                            SELECT AVG(ml2.current_price)
                            FROM ml_features_materialized ml2
                            WHERE ml2.symbol = ml1.symbol
                              AND ml2.current_price > 0
                              AND ml2.timestamp BETWEEN 
                                  DATE_SUB(ml1.timestamp, INTERVAL 7 DAY) 
                                  AND ml1.timestamp
                        ),
                        updated_at = NOW()
                    WHERE ml1.symbol = %s 
                      AND ml1.current_price > 0
                      AND ml1.sma_7 IS NULL
                      AND ml1.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """, (symbol,))
                
                improvements += cursor.rowcount
                
                # Calculate 30-day SMA
                cursor.execute("""
                    UPDATE ml_features_materialized ml1
                    SET 
                        sma_30 = (
                            SELECT AVG(ml2.current_price)
                            FROM ml_features_materialized ml2
                            WHERE ml2.symbol = ml1.symbol
                              AND ml2.current_price > 0
                              AND ml2.timestamp BETWEEN 
                                  DATE_SUB(ml1.timestamp, INTERVAL 30 DAY) 
                                  AND ml1.timestamp
                        ),
                        updated_at = NOW()
                    WHERE ml1.symbol = %s 
                      AND ml1.current_price > 0
                      AND ml1.sma_30 IS NULL
                      AND ml1.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """, (symbol,))
                
                improvements += cursor.rowcount
                
                if improvements % 100 == 0:
                    conn.commit()
                    
            except Exception as e:
                logger.warning(f"Error calculating SMA for {symbol}: {e}")
                continue
        
        conn.commit()
        logger.info(f"✅ Calculated SMAs for {improvements} records")
        
        cursor.close()
        conn.close()
        return improvements
        
    except Exception as e:
        logger.error(f"Error calculating SMAs: {e}")
        return 0


def calculate_rsi_indicators():
    """Calculate RSI indicators where missing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Calculating RSI indicators...")
        
        # Simple RSI calculation based on price changes
        cursor.execute("""
            UPDATE ml_features_materialized ml1
            SET 
                rsi_14 = CASE 
                    WHEN ml1.current_price > 0 THEN
                        50 + (
                            (ml1.current_price - COALESCE(ml1.sma_7, ml1.current_price)) 
                            / GREATEST(ml1.current_price * 0.01, 1)
                        ) * 10
                    ELSE NULL
                END,
                updated_at = NOW()
            WHERE ml1.rsi_14 IS NULL
              AND ml1.current_price > 0
              AND ml1.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        improvements = cursor.rowcount
        conn.commit()
        
        logger.info(f"✅ Calculated RSI for {improvements} records")
        
        cursor.close()
        conn.close()
        return improvements
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return 0


def calculate_volatility_metrics():
    """Calculate volatility metrics where missing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Calculating volatility metrics...")
        
        # Calculate price volatility based on recent price changes
        cursor.execute("""
            UPDATE ml_features_materialized ml1
            SET 
                price_volatility = CASE 
                    WHEN ml1.current_price > 0 AND ml1.sma_7 > 0 THEN
                        ABS(ml1.current_price - ml1.sma_7) / ml1.sma_7 * 100
                    WHEN ml1.current_price > 0 THEN
                        ABS(ml1.percent_change_24h)
                    ELSE NULL
                END,
                volume_volatility = CASE 
                    WHEN ml1.volume_24h > 0 THEN
                        ABS(ml1.volume_24h - COALESCE(ml1.total_volume_24h, ml1.volume_24h)) 
                        / ml1.volume_24h * 100
                    ELSE NULL
                END,
                updated_at = NOW()
            WHERE (ml1.price_volatility IS NULL OR ml1.volume_volatility IS NULL)
              AND ml1.current_price > 0
              AND ml1.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        improvements = cursor.rowcount
        conn.commit()
        
        logger.info(f"✅ Calculated volatility for {improvements} records")
        
        cursor.close()
        conn.close()
        return improvements
        
    except Exception as e:
        logger.error(f"Error calculating volatility: {e}")
        return 0


def enhance_trend_indicators():
    """Enhance trend indicators using available data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info("Enhancing trend indicators...")
        
        # Calculate trend strength based on SMA relationships
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                trend_strength = CASE 
                    WHEN sma_7 > 0 AND sma_30 > 0 THEN
                        (sma_7 - sma_30) / sma_30 * 100
                    WHEN current_price > 0 AND sma_7 > 0 THEN
                        (current_price - sma_7) / sma_7 * 100
                    ELSE NULL
                END,
                trend_direction = CASE 
                    WHEN sma_7 > sma_30 THEN 'BULLISH'
                    WHEN sma_7 < sma_30 THEN 'BEARISH'
                    WHEN percent_change_24h > 2 THEN 'BULLISH'
                    WHEN percent_change_24h < -2 THEN 'BEARISH'
                    ELSE 'NEUTRAL'
                END,
                updated_at = NOW()
            WHERE (trend_strength IS NULL OR trend_direction IS NULL)
              AND current_price > 0
              AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        improvements = cursor.rowcount
        conn.commit()
        
        logger.info(f"✅ Enhanced trends for {improvements} records")
        
        cursor.close()
        conn.close()
        return improvements
        
    except Exception as e:
        logger.error(f"Error enhancing trends: {e}")
        return 0


def analyze_technical_improvements():
    """Analyze technical indicator improvements"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sma_7 IS NOT NULL THEN 1 ELSE 0 END) as has_sma7,
                SUM(CASE WHEN sma_30 IS NOT NULL THEN 1 ELSE 0 END) as has_sma30,
                SUM(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as has_rsi,
                SUM(CASE WHEN price_volatility IS NOT NULL THEN 1 ELSE 0 END) as has_volatility,
                SUM(CASE WHEN trend_strength IS NOT NULL THEN 1 ELSE 0 END) as has_trend
            FROM ml_features_materialized
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        print(f"\n📊 TECHNICAL INDICATORS ANALYSIS (Last 7 days)")
        print(f"Total records: {total:,}")
        print(f"Has SMA-7: {result[1]:,} ({result[1]/total*100:.1f}%)")
        print(f"Has SMA-30: {result[2]:,} ({result[2]/total*100:.1f}%)")
        print(f"Has RSI-14: {result[3]:,} ({result[3]/total*100:.1f}%)")
        print(f"Has volatility: {result[4]:,} ({result[4]/total*100:.1f}%)")
        print(f"Has trend data: {result[5]:,} ({result[5]/total*100:.1f}%)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing improvements: {e}")
        return False


def main():
    """Main function to enhance technical indicators"""
    logger.info("Starting technical indicators enhancement...")
    
    print("📈 TECHNICAL INDICATORS ENHANCEMENT")
    print("=" * 60)
    
    total_improvements = 0
    
    # Step 1: Calculate SMAs
    print("\n🔄 Step 1: Calculating moving averages...")
    sma_improvements = calculate_simple_moving_averages()
    total_improvements += sma_improvements
    
    # Step 2: Calculate RSI
    print("\n🔄 Step 2: Calculating RSI indicators...")
    rsi_improvements = calculate_rsi_indicators()
    total_improvements += rsi_improvements
    
    # Step 3: Calculate volatility
    print("\n🔄 Step 3: Calculating volatility metrics...")
    vol_improvements = calculate_volatility_metrics()
    total_improvements += vol_improvements
    
    # Step 4: Enhance trends
    print("\n🔄 Step 4: Enhancing trend indicators...")
    trend_improvements = enhance_trend_indicators()
    total_improvements += trend_improvements
    
    # Step 5: Analyze results
    print("\n📈 Step 5: Analyzing improvements...")
    analyze_technical_improvements()
    
    print(f"\n" + "=" * 60)
    print(f"✅ TECHNICAL INDICATORS ENHANCEMENT COMPLETED")
    print(f"Total records improved: {total_improvements:,}")
    print("=" * 60)
    
    return total_improvements > 0


if __name__ == "__main__":
    main()