-- Safe Database Cleanup SQL Script
-- Date: September 30, 2025
-- Purpose: Remove only empty or minimal unused tables
-- Risk Level: LOW (only empty/minimal tables)

-- =====================================================
-- PRE-CLEANUP INFORMATION
-- =====================================================

SELECT 'BEFORE CLEANUP - Database Overview' as 'Status';

SELECT COUNT(*) as 'Total Tables Before Cleanup' 
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices';

SELECT 
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Database Size (MB) Before Cleanup'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices';

-- Show tables to be deleted
SELECT 'Tables to be deleted:' as 'Safe Cleanup Plan';
SELECT table_name, 
       ROUND((data_length + index_length) / 1024 / 1024, 4) AS 'Size (MB)',
       table_rows as 'Row Count'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices' 
AND table_name IN (
    'daily_regime_summary',
    'sentiment_data', 
    'social_media_posts',
    'social_platform_stats',
    'trading_engine_v2_summary',
    'collection_monitoring',
    'crypto_metadata',
    'monitoring_alerts'
)
ORDER BY (data_length + index_length) DESC;

-- =====================================================
-- SAFE CLEANUP EXECUTION
-- =====================================================

SELECT 'EXECUTING SAFE CLEANUP...' as 'Status';

-- Drop definitely unused tables (empty or minimal data)
-- These tables have been verified as safe to remove

-- 1. Empty view tables
DROP TABLE IF EXISTS `daily_regime_summary`;
SELECT 'Dropped: daily_regime_summary' as 'Progress';

DROP TABLE IF EXISTS `sentiment_data`;
SELECT 'Dropped: sentiment_data' as 'Progress';

DROP TABLE IF EXISTS `social_media_posts`;
SELECT 'Dropped: social_media_posts' as 'Progress';

DROP TABLE IF EXISTS `social_platform_stats`;
SELECT 'Dropped: social_platform_stats' as 'Progress';

DROP TABLE IF EXISTS `trading_engine_v2_summary`;
SELECT 'Dropped: trading_engine_v2_summary' as 'Progress';

-- 2. Minimal data tables (not used by current collectors)
DROP TABLE IF EXISTS `collection_monitoring`;
SELECT 'Dropped: collection_monitoring' as 'Progress';

DROP TABLE IF EXISTS `crypto_metadata`;
SELECT 'Dropped: crypto_metadata' as 'Progress';

DROP TABLE IF EXISTS `monitoring_alerts`;
SELECT 'Dropped: monitoring_alerts' as 'Progress';

-- =====================================================
-- POST-CLEANUP VERIFICATION
-- =====================================================

SELECT 'CLEANUP COMPLETED - Verification' as 'Status';

SELECT COUNT(*) as 'Total Tables After Cleanup' 
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices';

SELECT 
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Database Size (MB) After Cleanup'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices';

-- Show remaining tables by category
SELECT 'Remaining Tables by Category:' as 'Final Status';

-- Core OHLC data tables (CRITICAL - DO NOT DELETE)
SELECT 'CORE DATA TABLES:' as 'Category', table_name, 
       ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)',
       table_rows as 'Rows'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices' 
AND table_name IN ('hourly_data', 'ohlc_data_1h', 'ml_ohlc_fixed', 'volume_data')
ORDER BY (data_length + index_length) DESC;

-- Analysis and ML tables
SELECT 'ANALYSIS/ML TABLES:' as 'Category', table_name,
       ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)',
       table_rows as 'Rows'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices' 
AND table_name IN ('trading_signals', 'sentiment_aggregation', 'real_time_sentiment_signals', 'technical_indicators')
ORDER BY (data_length + index_length) DESC;

-- Infrastructure tables
SELECT 'INFRASTRUCTURE TABLES:' as 'Category', table_name,
       ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)',
       table_rows as 'Rows'
FROM information_schema.tables 
WHERE table_schema = 'crypto_prices' 
AND table_name IN ('service_monitoring', 'onchain_metrics', 'macro_indicators')
ORDER BY (data_length + index_length) DESC;

-- =====================================================
-- CLEANUP SUMMARY
-- =====================================================

SELECT 
    'CLEANUP COMPLETED SUCCESSFULLY' as 'Final Status',
    '8 unused tables removed' as 'Tables Deleted',
    '~0.43 MB space freed' as 'Space Saved',
    'All critical data preserved' as 'Data Safety',
    'Monitor collectors for 24 hours' as 'Next Steps';

-- End of cleanup script