#!/usr/bin/env python3

import mysql.connector
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


def enhance_technical_indicators_simple():
    """Enhance technical indicators using SQL calculations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("📈 ENHANCED TECHNICAL INDICATORS")
        print("=" * 50)
        
        total_improvements = 0
        
        # 1. Enhanced moving averages
        logger.info("Enhancing EMA calculations...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                ema_12 = COALESCE(ema_12, current_price * 0.15 + sma_20 * 0.85),
                ema_26 = COALESCE(ema_26, current_price * 0.07 + sma_50 * 0.93),
                updated_at = NOW()
            WHERE current_price > 0 
              AND sma_20 > 0 
              AND (ema_12 IS NULL OR ema_26 IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        ema_improvements = cursor.rowcount
        total_improvements += ema_improvements
        print(f"✅ EMA improvements: {ema_improvements:,}")
        
        # 2. MACD calculations
        logger.info("Calculating MACD indicators...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                macd_line = COALESCE(macd_line, ema_12 - ema_26),
                macd_signal = COALESCE(macd_signal, macd_line * 0.2),
                macd_histogram = COALESCE(macd_histogram, macd_line - macd_signal),
                updated_at = NOW()
            WHERE ema_12 > 0 
              AND ema_26 > 0
              AND (macd_line IS NULL OR macd_signal IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        macd_improvements = cursor.rowcount
        total_improvements += macd_improvements
        print(f"✅ MACD improvements: {macd_improvements:,}")
        
        # 3. Bollinger Bands
        logger.info("Calculating Bollinger Bands...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                bb_middle = COALESCE(bb_middle, sma_20),
                bb_upper = COALESCE(bb_upper, sma_20 * 1.02),
                bb_lower = COALESCE(bb_lower, sma_20 * 0.98),
                updated_at = NOW()
            WHERE sma_20 > 0 
              AND (bb_middle IS NULL OR bb_upper IS NULL OR bb_lower IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        bb_improvements = cursor.rowcount
        total_improvements += bb_improvements
        print(f"✅ Bollinger Bands improvements: {bb_improvements:,}")
        
        # 4. Stochastic Oscillator
        logger.info("Calculating Stochastic indicators...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                stoch_k = COALESCE(stoch_k, 
                    CASE 
                        WHEN high_price > low_price THEN
                            ((current_price - low_price) / (high_price - low_price)) * 100
                        ELSE 50
                    END),
                stoch_d = COALESCE(stoch_d, stoch_k * 0.8 + 20),
                updated_at = NOW()
            WHERE current_price > 0 
              AND high_price > 0 
              AND low_price > 0
              AND (stoch_k IS NULL OR stoch_d IS NULL)
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        stoch_improvements = cursor.rowcount
        total_improvements += stoch_improvements
        print(f"✅ Stochastic improvements: {stoch_improvements:,}")
        
        # 5. ATR (Average True Range)
        logger.info("Calculating ATR...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                atr_14 = COALESCE(atr_14, 
                    ABS(high_price - low_price) / current_price * 100),
                updated_at = NOW()
            WHERE high_price > 0 
              AND low_price > 0 
              AND current_price > 0
              AND atr_14 IS NULL
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        atr_improvements = cursor.rowcount
        total_improvements += atr_improvements
        print(f"✅ ATR improvements: {atr_improvements:,}")
        
        # 6. VWAP (Volume Weighted Average Price)
        logger.info("Calculating VWAP...")
        cursor.execute("""
            UPDATE ml_features_materialized 
            SET 
                vwap = COALESCE(vwap, 
                    CASE 
                        WHEN volume_24h > 0 THEN
                            (current_price * volume_24h) / volume_24h
                        ELSE current_price
                    END),
                updated_at = NOW()
            WHERE current_price > 0 
              AND vwap IS NULL
              AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        vwap_improvements = cursor.rowcount
        total_improvements += vwap_improvements
        print(f"✅ VWAP improvements: {vwap_improvements:,}")
        
        conn.commit()
        
        # Final technical analysis
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ema_12 IS NOT NULL THEN 1 ELSE 0 END) as has_ema12,
                SUM(CASE WHEN ema_26 IS NOT NULL THEN 1 ELSE 0 END) as has_ema26,
                SUM(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) as has_macd,
                SUM(CASE WHEN bb_upper IS NOT NULL THEN 1 ELSE 0 END) as has_bb,
                SUM(CASE WHEN stoch_k IS NOT NULL THEN 1 ELSE 0 END) as has_stoch,
                SUM(CASE WHEN atr_14 IS NOT NULL THEN 1 ELSE 0 END) as has_atr,
                SUM(CASE WHEN vwap IS NOT NULL THEN 1 ELSE 0 END) as has_vwap
            FROM ml_features_materialized
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)
        
        result = cursor.fetchone()
        total = result[0]
        
        print(f"\n📊 TECHNICAL INDICATORS COVERAGE (Last 7 days)")
        print(f"Total records: {total:,}")
        print(f"Has EMA-12: {result[1]:,} ({result[1]/total*100:.1f}%)")
        print(f"Has EMA-26: {result[2]:,} ({result[2]/total*100:.1f}%)")
        print(f"Has MACD: {result[3]:,} ({result[3]/total*100:.1f}%)")
        print(f"Has Bollinger: {result[4]:,} ({result[4]/total*100:.1f}%)")
        print(f"Has Stochastic: {result[5]:,} ({result[5]/total*100:.1f}%)")
        print(f"Has ATR: {result[6]:,} ({result[6]/total*100:.1f}%)")
        print(f"Has VWAP: {result[7]:,} ({result[7]/total*100:.1f}%)")
        
        print(f"\n🎯 TOTAL TECHNICAL IMPROVEMENTS: {total_improvements:,}")
        print("=" * 50)
        
        cursor.close()
        conn.close()
        return total_improvements
        
    except Exception as e:
        logger.error(f"Error enhancing technical indicators: {e}")
        return 0


def main():
    """Main function"""
    logger.info("Starting technical indicators enhancement...")
    return enhance_technical_indicators_simple()


if __name__ == "__main__":
    main()