#!/bin/bash
# Database Schema Analysis via Kubernetes Pod
# Uses running collectors to analyze ml_features_materialized schema

echo "🔍 Analyzing ml_features_materialized table schema via K8s pods..."

# Find a running pod with database access
ML_MARKET_POD=$(kubectl get pods -n crypto-data-collection -l app=ml-market-collector -o jsonpath='{.items[0].metadata.name}')
DERIVATIVES_POD=$(kubectl get pods -n crypto-data-collection -l app=derivatives-collector -o jsonpath='{.items[0].metadata.name}')

if [ -n "$ML_MARKET_POD" ]; then
    ACTIVE_POD=$ML_MARKET_POD
    echo "✅ Using ML Market Collector pod: $ACTIVE_POD"
elif [ -n "$DERIVATIVES_POD" ]; then
    ACTIVE_POD=$DERIVATIVES_POD
    echo "✅ Using Derivatives Collector pod: $ACTIVE_POD"
else
    echo "❌ No suitable pods found"
    exit 1
fi

# Create database analysis script
cat > /tmp/db_schema_analysis.py << 'EOF'
import mysql.connector
import os
import json

# Database configuration from environment
db_config = {
    'user': os.getenv('MYSQL_USER', 'news_collector'),
    'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
    'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
    'charset': 'utf8mb4'
}

try:
    # Connect to database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Get ml_features_materialized schema
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COLUMN_COMMENT,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ml_features_materialized'
        ORDER BY ORDINAL_POSITION
    """, (db_config['database'],))
    
    schema_info = cursor.fetchall()
    
    if schema_info:
        print(f"📊 ml_features_materialized has {len(schema_info)} columns")
        print("=" * 80)
        
        for i, col in enumerate(schema_info, 1):
            nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['COLUMN_DEFAULT']}" if col['COLUMN_DEFAULT'] else ""
            comment = f"-- {col['COLUMN_COMMENT']}" if col['COLUMN_COMMENT'] else ""
            
            print(f"{i:3}. {col['COLUMN_NAME']:30} {col['DATA_TYPE']:15} {nullable:10} {default:15} {comment}")
    else:
        print("❌ Table ml_features_materialized not found or not accessible")
    
    # Get sample data coverage
    cursor.execute("SELECT COUNT(*) as total_rows FROM ml_features_materialized")
    total_rows = cursor.fetchone()['total_rows']
    
    print(f"\n📈 Total rows: {total_rows:,}")
    
    # Quick coverage analysis for key columns
    key_columns = ['price', 'volume', 'sentiment_score', 'rsi_14', 'active_addresses_24h', 
                   'vix', 'fed_funds_rate', 'funding_rate']
    
    print("\n🔍 Quick Coverage Analysis (last 100 records):")
    print("-" * 60)
    
    for column in key_columns:
        try:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({column}) as populated,
                    ROUND(COUNT({column}) * 100.0 / COUNT(*), 2) as coverage_pct
                FROM (
                    SELECT * FROM ml_features_materialized 
                    ORDER BY timestamp DESC LIMIT 100
                ) t
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"{column:25}: {result['coverage_pct']:6.1f}% ({result['populated']:3}/{result['total']:3} records)")
        except Exception as e:
            print(f"{column:25}: ❌ Column not found or error: {str(e)[:50]}")
    
    conn.close()
    print("\n✅ Schema analysis completed")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF

# Copy script to pod and execute
echo "📤 Copying analysis script to pod..."
kubectl cp /tmp/db_schema_analysis.py crypto-data-collection/$ACTIVE_POD:/tmp/db_schema_analysis.py

echo "🚀 Executing schema analysis..."
kubectl exec -n crypto-data-collection $ACTIVE_POD -- python3 /tmp/db_schema_analysis.py

echo "🧹 Cleaning up..."
rm -f /tmp/db_schema_analysis.py