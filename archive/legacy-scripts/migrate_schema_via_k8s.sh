#!/bin/bash
# Run Database Migration via Kubernetes Pod
# Executes the migration from within the cluster for database access

echo "🔍 Running ML features schema migration via K8s pod..."

# Find a running pod with database access
ML_MARKET_POD=$(kubectl get pods -n crypto-data-collection -l app=ml-market-collector -o jsonpath='{.items[0].metadata.name}')

if [ -n "$ML_MARKET_POD" ]; then
    echo "✅ Using ML Market Collector pod: $ML_MARKET_POD"
else
    echo "❌ No suitable pods found"
    exit 1
fi

# Create migration script for execution in pod
cat > /tmp/k8s_migrate_ml_features.py << 'EOF'
import mysql.connector
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using K8s environment"""
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "host.docker.internal"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
            charset="utf8mb4",
            autocommit=False
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
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

def add_key_ml_features():
    """Add essential ML feature columns (subset for initial implementation)"""
    
    # Start with essential columns
    essential_columns = [
        # Traditional Markets
        ("qqq_price", "DECIMAL(15,8)"),
        ("qqq_volume", "BIGINT"),
        ("qqq_rsi", "DECIMAL(5,2)"),
        ("arkk_price", "DECIMAL(15,8)"), 
        ("arkk_rsi", "DECIMAL(5,2)"),
        ("gold_futures", "DECIMAL(10,4)"),
        ("oil_wti", "DECIMAL(10,4)"),
        ("bond_10y_yield", "DECIMAL(6,4)"),
        ("usd_index", "DECIMAL(10,4)"),
        
        # ML Indicators
        ("market_correlation_crypto", "DECIMAL(6,4)"),
        ("volatility_regime", "DECIMAL(6,4)"),
        ("momentum_composite", "DECIMAL(6,4)"),
        
        # Derivatives Composites
        ("avg_funding_rate", "DECIMAL(10,8)"),
        ("total_open_interest", "DECIMAL(25,8)"),
        ("liquidation_ratio", "DECIMAL(8,4)"),
        ("derivatives_momentum", "DECIMAL(6,4)"),
        ("leverage_sentiment", "DECIMAL(6,4)"),
        
        # Key exchange data for BTC/ETH
        ("binance_btc_funding_rate", "DECIMAL(10,8)"),
        ("binance_btc_open_interest", "DECIMAL(20,8)"),
        ("binance_eth_funding_rate", "DECIMAL(10,8)"),
        ("binance_eth_open_interest", "DECIMAL(20,8)")
    ]
    
    logger.info(f"Starting migration to add {len(essential_columns)} essential ML columns")
    
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot connect to database")
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
        logger.info(f"Current column count: {current_columns}")
        
        added_count = 0
        skipped_count = 0
        
        # Add each column
        for column_name, column_type in essential_columns:
            if check_column_exists(cursor, 'ml_features_materialized', column_name):
                logger.info(f"Column {column_name} already exists, skipping")
                skipped_count += 1
                continue
            
            try:
                alter_sql = f"""
                ALTER TABLE ml_features_materialized 
                ADD COLUMN {column_name} {column_type} NULL
                """
                cursor.execute(alter_sql)
                conn.commit()
                logger.info(f"Added column: {column_name} ({column_type})")
                added_count += 1
            
            except mysql.connector.Error as e:
                logger.error(f"Failed to add column {column_name}: {e}")
                conn.rollback()
        
        # Final column count
        cursor.execute("""
            SELECT COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'ml_features_materialized'
        """)
        final_columns = cursor.fetchone()[0]
        
        logger.info(f"Migration Summary:")
        logger.info(f"   - Columns before: {current_columns}")
        logger.info(f"   - Columns added: {added_count}")
        logger.info(f"   - Columns skipped: {skipped_count}")
        logger.info(f"   - Columns after: {final_columns}")
        logger.info(f"Migration completed successfully!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    logger.info("ML Features Schema Migration Starting...")
    success = add_key_ml_features()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
EOF

# Copy script to pod and execute
echo "📤 Copying migration script to pod..."
kubectl cp /tmp/k8s_migrate_ml_features.py crypto-data-collection/$ML_MARKET_POD:/tmp/k8s_migrate_ml_features.py

echo "🚀 Executing migration..."
kubectl exec -n crypto-data-collection $ML_MARKET_POD -- python3 /tmp/k8s_migrate_ml_features.py

echo "🧹 Cleaning up..."
rm -f /tmp/k8s_migrate_ml_features.py