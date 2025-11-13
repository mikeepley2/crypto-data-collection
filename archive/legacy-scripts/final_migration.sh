#!/bin/bash
# Execute final migration and cleanup via MySQL command line

echo "=== EXECUTING FINAL MIGRATION AND CLEANUP ==="

# Database connection parameters
HOST="172.22.32.1"
USER="news_collector"
PASS="99Rules!"

# Step 1: Migrate unique news articles
echo "Step 1: Migrating unique news articles..."
mysql -h$HOST -u$USER -p$PASS -e "
USE crypto_news;
INSERT INTO news_data (title, content, url, published_date, source, sentiment_score, created_at)
SELECT 
    title, content, url, published_date, 
    COALESCE(source, 'migrated_from_crypto_prices'), 
    sentiment_score, NOW()
FROM crypto_prices.crypto_news cn
WHERE cn.url IS NOT NULL 
AND cn.url NOT IN (
    SELECT DISTINCT nd.url FROM crypto_news.news_data nd 
    WHERE nd.url IS NOT NULL
);
SELECT ROW_COUNT() as 'News articles migrated';
"

# Step 2: Archive duplicate tables
echo "Step 2: Archiving duplicate tables..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Archive tables one by one
mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_prices.crypto_news TO crypto_prices.crypto_news_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_prices.crypto_news"

mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_news.stock_market_news_data TO crypto_news.stock_market_news_data_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_news.stock_market_news_data"

mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_news.macro_economic_data TO crypto_news.macro_economic_data_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_news.macro_economic_data"

mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_prices.sentiment_aggregation TO crypto_prices.sentiment_aggregation_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_prices.sentiment_aggregation"

mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_news.crypto_sentiment_data TO crypto_news.crypto_sentiment_data_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_news.crypto_sentiment_data"

mysql -h$HOST -u$USER -p$PASS -e "RENAME TABLE crypto_news.social_sentiment_metrics TO crypto_news.social_sentiment_metrics_archive_${TIMESTAMP}_old;" 2>/dev/null && echo "  Archived crypto_news.social_sentiment_metrics"

# Step 3: Final verification
echo "Step 3: Final verification..."
mysql -h$HOST -u$USER -p$PASS -e "
SELECT 'PRIMARY TABLES STATUS:' as status;
SELECT 'Technical' as table_type, COUNT(*) as records FROM crypto_prices.technical_indicators
UNION ALL
SELECT 'News' as table_type, COUNT(*) as records FROM crypto_news.news_data  
UNION ALL
SELECT 'Macro' as table_type, COUNT(*) as records FROM crypto_prices.macro_indicators
UNION ALL
SELECT 'Onchain' as table_type, COUNT(*) as records FROM crypto_prices.crypto_onchain_data
UNION ALL
SELECT 'OHLC' as table_type, COUNT(*) as records FROM crypto_prices.ohlc_data
UNION ALL
SELECT 'ML Features' as table_type, COUNT(*) as records FROM crypto_prices.ml_features_materialized;
"

echo "=== MIGRATION AND CLEANUP COMPLETED ==="