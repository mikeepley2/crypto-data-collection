#!/usr/bin/env python3
"""
Test Script: Verify Materialized Updater Technical Indicators Integration
Tests that the materialized updater can correctly access and use the recovered
3.3M technical indicators for populating the ML features materialized table.
"""

import mysql.connector
import logging
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaterializedUpdaterTechnicalIndicatorsTest:
    """Test the materialized updater's technical indicators integration"""
    
    def __init__(self):
        self.db_config = {
            'host': '192.168.230.162',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
    
    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)
    
    def test_technical_indicators_access(self):
        """Test that technical indicators can be accessed correctly"""
        logger.info("Testing technical indicators access...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Test the corrected query format that the materialized updater should use
            test_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'ATOM']
            
            for symbol in test_symbols:
                # Query technical indicators using the correct format
                cursor.execute("""
                    SELECT 
                        symbol, timestamp_iso,
                        rsi_14, sma_20, sma_50, sma_30, sma_200, 
                        ema_12, ema_20, ema_26, ema_50, ema_200,
                        macd, macd_signal, macd_histogram,
                        bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap
                    FROM technical_indicators 
                    WHERE symbol = %s 
                    AND DATE(timestamp_iso) >= CURDATE() - INTERVAL 7 DAY
                    ORDER BY timestamp_iso DESC
                    LIMIT 10
                """, (symbol,))
                
                results = cursor.fetchall()
                
                if results:
                    logger.info(f"✅ {symbol}: Found {len(results)} technical indicators")
                    
                    # Check data quality
                    sample = results[0]
                    filled_fields = sum(1 for k, v in sample.items() if v is not None and k not in ['symbol', 'timestamp_iso'])
                    total_fields = len(sample) - 2  # Exclude symbol and timestamp
                    
                    logger.info(f"   Data quality: {filled_fields}/{total_fields} fields filled ({filled_fields/total_fields*100:.1f}%)")
                    logger.info(f"   Latest: {sample['timestamp_iso']} - RSI: {sample['rsi_14']}, SMA20: {sample['sma_20']}")
                    
                    # Verify key indicators are present
                    key_indicators = ['rsi_14', 'sma_20', 'macd', 'bb_upper']
                    missing = [ind for ind in key_indicators if sample.get(ind) is None]
                    if missing:
                        logger.warning(f"   Missing key indicators: {missing}")
                    else:
                        logger.info(f"   ✅ All key indicators present")
                else:
                    logger.warning(f"❌ {symbol}: No technical indicators found")
        
        except Exception as e:
            logger.error(f"Error testing technical indicators access: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def test_ml_features_integration(self):
        """Test integration with ml_features_materialized table"""
        logger.info("Testing ML features materialized integration...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check current state of ml_features_materialized
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as rsi_filled,
                    COUNT(CASE WHEN sma_20 IS NOT NULL THEN 1 END) as sma20_filled,
                    COUNT(CASE WHEN macd IS NOT NULL THEN 1 END) as macd_filled,
                    COUNT(CASE WHEN bb_upper IS NOT NULL THEN 1 END) as bb_filled
                FROM ml_features_materialized
                WHERE created_at >= CURDATE() - INTERVAL 7 DAY
            """)
            
            stats = cursor.fetchone()
            
            logger.info(f"📊 ML Features Materialized Stats (last 7 days):")
            logger.info(f"   Total records: {stats['total_records']:,}")
            
            if stats['total_records'] > 0:
                logger.info(f"   RSI filled: {stats['rsi_filled']:,} ({stats['rsi_filled']/stats['total_records']*100:.1f}%)")
                logger.info(f"   SMA20 filled: {stats['sma20_filled']:,} ({stats['sma20_filled']/stats['total_records']*100:.1f}%)")
                logger.info(f"   MACD filled: {stats['macd_filled']:,} ({stats['macd_filled']/stats['total_records']*100:.1f}%)")
                logger.info(f"   Bollinger filled: {stats['bb_filled']:,} ({stats['bb_filled']/stats['total_records']*100:.1f}%)")
                
                # Check for symbols with good technical indicator coverage
                cursor.execute("""
                    SELECT 
                        symbol,
                        COUNT(*) as records,
                        COUNT(CASE WHEN rsi_14 IS NOT NULL THEN 1 END) as rsi_count,
                        COUNT(CASE WHEN sma_20 IS NOT NULL THEN 1 END) as sma_count
                    FROM ml_features_materialized
                    WHERE created_at >= CURDATE() - INTERVAL 7 DAY
                    GROUP BY symbol
                    HAVING records >= 10
                    ORDER BY (rsi_count + sma_count) DESC
                    LIMIT 5
                """)
                
                top_symbols = cursor.fetchall()
                logger.info(f"🏆 Top symbols with technical indicators:")
                for sym in top_symbols:
                    coverage = (sym['rsi_count'] + sym['sma_count']) / (sym['records'] * 2) * 100
                    logger.info(f"   {sym['symbol']}: {coverage:.1f}% coverage ({sym['records']} records)")
            else:
                logger.warning("❌ No recent records in ml_features_materialized")
        
        except Exception as e:
            logger.error(f"Error testing ML features integration: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def test_materialized_updater_query_compatibility(self):
        """Test the exact query format used by materialized updater"""
        logger.info("Testing materialized updater query compatibility...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Test the exact query format from the materialized updater
            symbol = 'BTC'
            start_date = datetime.now().date() - timedelta(days=3)
            end_date = datetime.now().date()
            
            # This is the corrected query from the materialized updater
            tech_query = """
            SELECT 
                symbol, timestamp_iso,
                rsi_14, sma_20, sma_50, sma_30, sma_200, ema_12, ema_20, ema_26, ema_50, ema_200,
                macd, macd_signal, macd_histogram,
                bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap
            FROM technical_indicators 
            WHERE symbol = %s 
            AND DATE(timestamp_iso) >= %s AND DATE(timestamp_iso) <= %s
            """
            
            cursor.execute(tech_query, (symbol, start_date, end_date))
            results = cursor.fetchall()
            
            if results:
                logger.info(f"✅ Materialized updater query compatible: {len(results)} records found for {symbol}")
                
                # Test the lookup logic
                tech_lookup = {}
                for row in results:
                    key = (row['timestamp_iso'].date(), row['timestamp_iso'].hour)
                    tech_lookup[key] = row
                
                logger.info(f"   Created lookup table with {len(tech_lookup)} hourly entries")
                
                # Test a specific lookup
                if tech_lookup:
                    sample_key = list(tech_lookup.keys())[0]
                    sample_data = tech_lookup[sample_key]
                    logger.info(f"   Sample lookup ({sample_key}): RSI={sample_data['rsi_14']}, SMA20={sample_data['sma_20']}")
                    logger.info(f"   ✅ Lookup mechanism working correctly")
                else:
                    logger.warning("❌ No data available for lookup testing")
            else:
                logger.warning(f"❌ No technical indicators found for {symbol} in date range")
        
        except Exception as e:
            logger.error(f"Error testing materialized updater compatibility: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def run_comprehensive_test(self):
        """Run all tests"""
        logger.info("=== MATERIALIZED UPDATER TECHNICAL INDICATORS INTEGRATION TEST ===")
        
        print("\n🔍 Testing Technical Indicators Access...")
        self.test_technical_indicators_access()
        
        print("\n📊 Testing ML Features Integration...")
        self.test_ml_features_integration()
        
        print("\n🔧 Testing Materialized Updater Compatibility...")
        self.test_materialized_updater_query_compatibility()
        
        logger.info("=== TEST COMPLETE ===")

if __name__ == "__main__":
    tester = MaterializedUpdaterTechnicalIndicatorsTest()
    tester.run_comprehensive_test()