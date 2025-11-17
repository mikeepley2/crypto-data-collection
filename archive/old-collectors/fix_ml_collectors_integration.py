#!/usr/bin/env python3
"""
Fix ML Collectors Integration
Create bridge between ML collectors and ml_features_materialized table
Populate the 88 new ML columns from existing collector data
"""

import mysql.connector
import requests
import json
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ml-integration-fixer')

class MLCollectorsIntegrationFixer:
    """Fix the integration between ML collectors and materialized table"""
    
    def __init__(self):
        self.db_config = {
            'host': 'postgres-cluster-rw.postgres-operator.svc.cluster.local',
            'user': 'crypto_user',
            'password': 'crypto_secure_password_2024',
            'database': 'crypto_data'
        }
        
        # ML Market Collector mapping (localhost:8080 data -> ml_features_materialized columns)
        self.ml_market_mappings = {
            # Traditional Markets (from ML Market Collector)
            'qqq_price': 'ML_QQQ_PRICE',
            'qqq_volume': 'ML_QQQ_VOLUME', 
            'qqq_rsi': 'ML_QQQ_RSI',
            'arkk_price': 'ML_ARKK_PRICE',
            'arkk_rsi': 'ML_ARKK_RSI',
            'gold_futures': 'ML_GOLD_PRICE',
            'oil_wti': 'ML_OIL_PRICE',
            'bond_10y_yield': 'ML_BOND_10Y',
            'usd_index': 'ML_USD_INDEX',
            
            # ML Indicators from Market Collector
            'market_correlation_crypto': 'ML_MARKET_CORRELATION_CRYPTO',
            'volatility_regime': 'ML_VOLATILITY_REGIME', 
            'momentum_composite': 'ML_MOMENTUM_COMPOSITE'
        }
        
        # Derivatives Collector mapping (localhost:8081 data -> ml_features_materialized columns)
        self.derivatives_mappings = {
            'avg_funding_rate': 'avg_funding_rate',
            'total_open_interest': 'total_open_interest',
            'liquidation_ratio': 'liquidation_ratio',
            'derivatives_momentum': 'derivatives_momentum',
            'leverage_sentiment': 'leverage_sentiment',
            'binance_btc_funding_rate': 'binance_btc_funding_rate',
            'binance_btc_open_interest': 'binance_btc_open_interest'
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def check_table_schemas(self):
        """Check current table schemas"""
        logger.info("🔍 Checking database schemas...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check macro_indicators schema
            logger.info("📊 Checking macro_indicators table...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'crypto_data' AND table_name = 'macro_indicators'
                ORDER BY ordinal_position
            """)
            macro_columns = cursor.fetchall()
            logger.info(f"macro_indicators has {len(macro_columns)} columns")
            
            # Check if source column exists
            has_source = any(col['column_name'] == 'source' for col in macro_columns)
            has_metadata = any(col['column_name'] == 'metadata' for col in macro_columns)
            
            logger.info(f"   - Has 'source' column: {has_source}")
            logger.info(f"   - Has 'metadata' column: {has_metadata}")
            
            if not has_source:
                logger.info("⚠️ Adding missing 'source' column to macro_indicators...")
                cursor.execute("ALTER TABLE macro_indicators ADD COLUMN source VARCHAR(255) DEFAULT 'unknown'")
            
            if not has_metadata:
                logger.info("⚠️ Adding missing 'metadata' column to macro_indicators...")
                cursor.execute("ALTER TABLE macro_indicators ADD COLUMN metadata TEXT")
            
            # Check ML columns in ml_features_materialized
            logger.info("📊 Checking ml_features_materialized ML columns...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'crypto_data' AND table_name = 'ml_features_materialized'
                AND column_name IN ('qqq_price', 'arkk_price', 'avg_funding_rate', 'binance_btc_funding_rate')
            """)
            ml_columns = cursor.fetchall()
            logger.info(f"Found {len(ml_columns)} sample ML columns in materialized table")
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Schema check failed: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def trigger_ml_collections(self):
        """Trigger both ML collectors to collect fresh data"""
        logger.info("🚀 Triggering ML collector data collection...")
        
        # Trigger ML Market Collector
        try:
            response = requests.post('http://localhost:8080/collect', timeout=30)
            if response.status_code == 200:
                logger.info("✅ ML Market Collector triggered successfully")
            else:
                logger.error(f"❌ ML Market Collector trigger failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to trigger ML Market Collector: {e}")
        
        # Trigger Derivatives Collector  
        try:
            response = requests.post('http://localhost:8081/collect', timeout=30)
            if response.status_code == 200:
                logger.info("✅ Derivatives Collector triggered successfully") 
            else:
                logger.error(f"❌ Derivatives Collector trigger failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to trigger Derivatives Collector: {e}")
    
    def read_ml_market_data(self):
        """Read ML market data from macro_indicators table"""
        logger.info("📊 Reading ML market data from macro_indicators...")
        
        conn = self.get_db_connection()
        if not conn:
            return {}
            
        cursor = conn.cursor(dictionary=True)
        ml_data = {}
        
        try:
            # Get latest ML market data
            cursor.execute("""
                SELECT indicator_name, value, indicator_date
                FROM macro_indicators 
                WHERE source = 'ML_Market_Collector' 
                AND indicator_date >= %s
                ORDER BY indicator_date DESC, updated_at DESC
            """, (datetime.now().date(),))
            
            records = cursor.fetchall()
            logger.info(f"Found {len(records)} ML market records from today")
            
            for record in records:
                ml_data[record['indicator_name']] = record['value']
                
            return ml_data
            
        except Exception as e:
            logger.error(f"Failed to read ML market data: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def read_derivatives_data(self):
        """Read derivatives data from API or database"""
        logger.info("⚡ Reading derivatives data...")
        
        try:
            # Try to get from derivatives collector API
            response = requests.get('http://localhost:8081/derivatives-features', timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got derivatives data from API: {len(data)} features")
                return data
            else:
                logger.warning("⚠️ Derivatives collector API not responding")
                return {}
        except Exception as e:
            logger.warning(f"⚠️ Failed to read derivatives data: {e}")
            return {}
    
    def update_materialized_table_ml_columns(self, ml_market_data, derivatives_data):
        """Update ml_features_materialized with ML collector data"""
        logger.info("🔄 Updating materialized table with ML data...")
        
        conn = self.get_db_connection()
        if not conn:
            return 0
            
        cursor = conn.cursor()
        updated_records = 0
        
        try:
            # Get recent records to update (last 24 hours)
            cursor.execute("""
                SELECT DISTINCT symbol, price_date 
                FROM ml_features_materialized 
                WHERE timestamp_utc >= %s
            """, (datetime.now() - timedelta(hours=24),))
            
            target_records = cursor.fetchall()
            logger.info(f"Found {len(target_records)} recent records to update")
            
            for symbol, price_date in target_records:
                update_values = {}
                
                # Map ML Market data
                for ml_column, indicator_name in self.ml_market_mappings.items():
                    if indicator_name in ml_market_data:
                        update_values[ml_column] = ml_market_data[indicator_name]
                
                # Map Derivatives data (if available)
                for ml_column, api_field in self.derivatives_mappings.items():
                    if api_field in derivatives_data:
                        update_values[ml_column] = derivatives_data[api_field]
                
                if update_values:
                    # Build dynamic UPDATE query
                    set_clause = ', '.join([f"{col} = %s" for col in update_values.keys()])
                    values = list(update_values.values())
                    values.extend([symbol, price_date])  # WHERE clause values
                    
                    query = f"""
                        UPDATE ml_features_materialized 
                        SET {set_clause}, updated_at = NOW()
                        WHERE symbol = %s AND price_date = %s
                    """
                    
                    cursor.execute(query, values)
                    updated_records += cursor.rowcount
            
            conn.commit()
            logger.info(f"✅ Updated {updated_records} records with ML data")
            return updated_records
            
        except Exception as e:
            logger.error(f"❌ Failed to update materialized table: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def verify_ml_data_population(self):
        """Verify that ML columns are now populated"""
        logger.info("🔍 Verifying ML data population...")
        
        conn = self.get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check sample ML columns for data
            sample_columns = ['qqq_price', 'arkk_price', 'avg_funding_rate']
            
            for column in sample_columns:
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT({column}) as populated_records,
                        MAX({column}) as max_value,
                        AVG({column}) as avg_value
                    FROM ml_features_materialized 
                    WHERE timestamp_utc >= %s
                """, (datetime.now() - timedelta(hours=24),))
                
                result = cursor.fetchone()
                if result:
                    pct_populated = (result['populated_records'] / result['total_records'] * 100) if result['total_records'] > 0 else 0
                    logger.info(f"   {column}: {result['populated_records']}/{result['total_records']} ({pct_populated:.1f}%) populated")
                    if result['max_value']:
                        logger.info(f"      Max: {result['max_value']:.4f}, Avg: {result['avg_value']:.4f}")
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def run_integration_fix(self):
        """Run the complete integration fix"""
        logger.info("🔧 Starting ML Collectors Integration Fix")
        logger.info("=" * 60)
        
        # 1. Check and fix database schemas
        if not self.check_table_schemas():
            logger.error("❌ Schema check failed, aborting")
            return
        
        # 2. Trigger fresh data collection
        self.trigger_ml_collections()
        
        # 3. Wait for collection to complete
        import time
        logger.info("⏳ Waiting 30 seconds for collection to complete...")
        time.sleep(30)
        
        # 4. Read collected data
        ml_market_data = self.read_ml_market_data()
        derivatives_data = self.read_derivatives_data()
        
        logger.info(f"📊 ML Market data points: {len(ml_market_data)}")
        logger.info(f"⚡ Derivatives data points: {len(derivatives_data)}")
        
        # 5. Update materialized table
        updated_count = self.update_materialized_table_ml_columns(ml_market_data, derivatives_data)
        
        # 6. Verify results
        if updated_count > 0:
            self.verify_ml_data_population()
            logger.info(f"✅ ML integration fix completed! Updated {updated_count} records")
        else:
            logger.error("❌ No records were updated - check data collection")

if __name__ == "__main__":
    fixer = MLCollectorsIntegrationFixer()
    fixer.run_integration_fix()