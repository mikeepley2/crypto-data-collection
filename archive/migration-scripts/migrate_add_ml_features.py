#!/usr/bin/env python3
"""
Database Schema Migration: Add 88 ML Features to ml_features_materialized
Adds columns for ML Market Collector (41 features) and Derivatives Collector (47 features)
"""

import mysql.connector
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "192.168.230.163"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
            charset="utf8mb4",
            autocommit=False
        )
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in the table"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s 
        AND COLUMN_NAME = %s
    """, (table_name, column_name))
    return cursor.fetchone()[0] > 0

def add_ml_features_columns():
    """Add all 88 ML feature columns to ml_features_materialized"""
    
    # ML Market Features (41 columns)
    ml_market_columns = [
        # Traditional ETFs - QQQ
        ("qqq_price", "DECIMAL(15,8)"),
        ("qqq_volume", "BIGINT"),
        ("qqq_rsi", "DECIMAL(5,2)"),
        ("qqq_sma_20", "DECIMAL(15,8)"),
        ("qqq_ema_12", "DECIMAL(15,8)"),
        
        # ARKK
        ("arkk_price", "DECIMAL(15,8)"),
        ("arkk_volume", "BIGINT"),
        ("arkk_rsi", "DECIMAL(5,2)"),
        ("arkk_sma_20", "DECIMAL(15,8)"),
        ("arkk_ema_12", "DECIMAL(15,8)"),
        
        # XLE
        ("xle_price", "DECIMAL(15,8)"),
        ("xle_volume", "BIGINT"),
        ("xle_rsi", "DECIMAL(5,2)"),
        ("xle_sma_20", "DECIMAL(15,8)"),
        
        # XLF
        ("xlf_price", "DECIMAL(15,8)"),
        ("xlf_volume", "BIGINT"),
        ("xlf_rsi", "DECIMAL(5,2)"),
        ("xlf_sma_20", "DECIMAL(15,8)"),
        
        # GLD
        ("gld_price", "DECIMAL(15,8)"),
        ("gld_volume", "BIGINT"),
        ("gld_rsi", "DECIMAL(5,2)"),
        ("gld_sma_20", "DECIMAL(15,8)"),
        
        # TLT
        ("tlt_price", "DECIMAL(15,8)"),
        ("tlt_volume", "BIGINT"),
        ("tlt_rsi", "DECIMAL(5,2)"),
        ("tlt_sma_20", "DECIMAL(15,8)"),
        
        # Market Indices & Commodities
        ("usd_index", "DECIMAL(10,4)"),
        ("nasdaq_100", "DECIMAL(15,8)"),
        ("nasdaq_volume", "BIGINT"),
        ("gold_futures", "DECIMAL(10,4)"),
        ("oil_wti", "DECIMAL(10,4)"),
        ("bond_10y_yield", "DECIMAL(6,4)"),
        ("bond_2y_yield", "DECIMAL(6,4)"),
        ("copper_futures", "DECIMAL(10,4)"),
        
        # ML Indicators
        ("market_correlation_crypto", "DECIMAL(6,4)"),
        ("sector_rotation_factor", "DECIMAL(6,4)"),
        ("risk_parity_score", "DECIMAL(6,4)"),
        ("momentum_composite", "DECIMAL(6,4)"),
        ("value_growth_ratio", "DECIMAL(6,4)"),
        ("volatility_regime", "DECIMAL(6,4)"),
        ("liquidity_stress_index", "DECIMAL(6,4)")
    ]
    
    # Derivatives Features (47 columns) - Simplified to key exchanges & composites
    derivatives_columns = [
        # Binance BTC
        ("binance_btc_funding_rate", "DECIMAL(10,8)"),
        ("binance_btc_open_interest", "DECIMAL(20,8)"),
        ("binance_btc_liquidations_long", "DECIMAL(20,8)"),
        ("binance_btc_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance ETH
        ("binance_eth_funding_rate", "DECIMAL(10,8)"),
        ("binance_eth_open_interest", "DECIMAL(20,8)"),
        ("binance_eth_liquidations_long", "DECIMAL(20,8)"),
        ("binance_eth_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance ADA
        ("binance_ada_funding_rate", "DECIMAL(10,8)"),
        ("binance_ada_open_interest", "DECIMAL(20,8)"),
        ("binance_ada_liquidations_long", "DECIMAL(20,8)"),
        ("binance_ada_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance SOL
        ("binance_sol_funding_rate", "DECIMAL(10,8)"),
        ("binance_sol_open_interest", "DECIMAL(20,8)"),
        ("binance_sol_liquidations_long", "DECIMAL(20,8)"),
        ("binance_sol_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance MATIC
        ("binance_matic_funding_rate", "DECIMAL(10,8)"),
        ("binance_matic_open_interest", "DECIMAL(20,8)"),
        ("binance_matic_liquidations_long", "DECIMAL(20,8)"),
        ("binance_matic_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance AVAX
        ("binance_avax_funding_rate", "DECIMAL(10,8)"),
        ("binance_avax_open_interest", "DECIMAL(20,8)"),
        ("binance_avax_liquidations_long", "DECIMAL(20,8)"),
        ("binance_avax_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance DOT
        ("binance_dot_funding_rate", "DECIMAL(10,8)"),
        ("binance_dot_open_interest", "DECIMAL(20,8)"),
        ("binance_dot_liquidations_long", "DECIMAL(20,8)"),
        ("binance_dot_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance LINK
        ("binance_link_funding_rate", "DECIMAL(10,8)"),
        ("binance_link_open_interest", "DECIMAL(20,8)"),
        ("binance_link_liquidations_long", "DECIMAL(20,8)"),
        ("binance_link_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance LTC
        ("binance_ltc_funding_rate", "DECIMAL(10,8)"),
        ("binance_ltc_open_interest", "DECIMAL(20,8)"),
        ("binance_ltc_liquidations_long", "DECIMAL(20,8)"),
        ("binance_ltc_liquidations_short", "DECIMAL(20,8)"),
        
        # Binance XRP
        ("binance_xrp_funding_rate", "DECIMAL(10,8)"),
        ("binance_xrp_open_interest", "DECIMAL(20,8)"),
        ("binance_xrp_liquidations_long", "DECIMAL(20,8)"),
        ("binance_xrp_liquidations_short", "DECIMAL(20,8)"),
        
        # Composite Derivatives Features
        ("avg_funding_rate", "DECIMAL(10,8)"),
        ("total_open_interest", "DECIMAL(25,8)"),
        ("liquidation_ratio", "DECIMAL(8,4)"),
        ("funding_divergence", "DECIMAL(8,4)"),
        ("derivatives_momentum", "DECIMAL(6,4)"),
        ("leverage_sentiment", "DECIMAL(6,4)"),
        ("market_stress_indicator", "DECIMAL(6,4)")
    ]
    
    # Combine all columns
    all_new_columns = ml_market_columns + derivatives_columns
    
    logger.info(f"🚀 Starting migration to add {len(all_new_columns)} ML feature columns")
    
    conn = get_db_connection()
    if not conn:
        logger.error("❌ Cannot connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check current column count
        cursor.execute("""
            SELECT COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ml_features_materialized'
        """)
        current_columns = cursor.fetchone()[0]
        logger.info(f"📊 Current column count: {current_columns}")
        
        added_count = 0
        skipped_count = 0
        
        # Add each column
        for column_name, column_type in all_new_columns:
            if check_column_exists(cursor, 'ml_features_materialized', column_name):
                logger.info(f"⏭️  Column {column_name} already exists, skipping")
                skipped_count += 1
                continue
            
            try:
                alter_sql = f"""
                ALTER TABLE ml_features_materialized 
                ADD COLUMN {column_name} {column_type} NULL
                """
                cursor.execute(alter_sql)
                conn.commit()
                logger.info(f"✅ Added column: {column_name} ({column_type})")
                added_count += 1
            
            except mysql.connector.Error as e:
                logger.error(f"❌ Failed to add column {column_name}: {e}")
                conn.rollback()
        
        # Final column count
        cursor.execute("""
            SELECT COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ml_features_materialized'
        """)
        final_columns = cursor.fetchone()[0]
        
        logger.info(f"📊 Migration Summary:")
        logger.info(f"   - Columns before: {current_columns}")
        logger.info(f"   - Columns added: {added_count}")
        logger.info(f"   - Columns skipped: {skipped_count}")
        logger.info(f"   - Columns after: {final_columns}")
        logger.info(f"✅ Migration completed successfully!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

def verify_schema():
    """Verify the updated schema"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all ML-related columns
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ml_features_materialized'
            AND (COLUMN_NAME LIKE '%qqq%' 
                 OR COLUMN_NAME LIKE '%arkk%'
                 OR COLUMN_NAME LIKE '%funding%'
                 OR COLUMN_NAME LIKE '%liquidation%'
                 OR COLUMN_NAME LIKE '%market_correlation%'
                 OR COLUMN_NAME LIKE '%derivatives%')
            ORDER BY COLUMN_NAME
        """)
        
        ml_columns = cursor.fetchall()
        logger.info(f"🔍 Found {len(ml_columns)} ML feature columns:")
        
        for col in ml_columns:
            logger.info(f"   - {col['COLUMN_NAME']}: {col['DATA_TYPE']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 ML Features Schema Migration Starting...")
    
    # Run migration
    success = add_ml_features_columns()
    
    if success:
        logger.info("🔍 Verifying updated schema...")
        verify_schema()
        logger.info("✅ Migration and verification completed!")
    else:
        logger.error("❌ Migration failed!")
    
    logger.info("🏁 Migration script completed")