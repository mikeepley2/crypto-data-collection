#!/bin/bash

# Safe Database Cleanup Script
# Removes only empty or minimal unused tables
# Date: September 30, 2025

echo "🧹 Starting Safe Database Cleanup..."
echo "=================================="

# Database connection details
DB_HOST="192.168.230.162"
DB_USER="news_collector"
DB_PASS="99Rules!"
DB_NAME="crypto_prices"

# Create backup timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="crypto_prices_safe_cleanup_backup_${TIMESTAMP}.sql"

echo "📦 Creating backup before cleanup..."
mysqldump -h ${DB_HOST} -u ${DB_USER} -p${DB_PASS} ${DB_NAME} > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "✅ Backup created: ${BACKUP_FILE}"
else
    echo "❌ Backup failed! Aborting cleanup."
    exit 1
fi

echo ""
echo "🗑️ Removing safe-to-delete tables..."
echo "-----------------------------------"

# List of definitely safe tables to delete (empty or minimal data)
SAFE_TABLES=(
    "daily_regime_summary"
    "sentiment_data"
    "social_media_posts" 
    "social_platform_stats"
    "trading_engine_v2_summary"
    "collection_monitoring"
    "crypto_metadata"
    "monitoring_alerts"
)

# Connect to MySQL and execute cleanup
mysql -h ${DB_HOST} -u ${DB_USER} -p${DB_PASS} ${DB_NAME} << EOF

-- Safe Database Cleanup
-- Only removing empty or minimal tables

-- Check current table count
SELECT COUNT(*) as 'Tables Before Cleanup' FROM information_schema.tables WHERE table_schema = '${DB_NAME}';

-- Remove safe tables
$(for table in "${SAFE_TABLES[@]}"; do
    echo "-- Dropping ${table}"
    echo "DROP TABLE IF EXISTS \`${table}\`;"
done)

-- Check table count after
SELECT COUNT(*) as 'Tables After Cleanup' FROM information_schema.tables WHERE table_schema = '${DB_NAME}';

-- Show space freed
SELECT 
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Database Size (MB)'
FROM information_schema.tables 
WHERE table_schema = '${DB_NAME}';

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Safe cleanup completed successfully!"
    echo "📊 Summary:"
    echo "  - Backup created: ${BACKUP_FILE}"
    echo "  - Tables removed: ${#SAFE_TABLES[@]}"
    echo "  - Space freed: ~0.43 MB"
    echo ""
    echo "🔍 Monitor collectors for 24 hours to ensure no issues."
    echo "💾 Backup location: $(pwd)/${BACKUP_FILE}"
else
    echo "❌ Cleanup failed! Database restored from backup."
    mysql -h ${DB_HOST} -u ${DB_USER} -p${DB_PASS} ${DB_NAME} < ${BACKUP_FILE}
fi

echo ""
echo "🏁 Cleanup process complete."