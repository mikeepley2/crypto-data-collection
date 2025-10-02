-- Database cleanup script
-- Generated on 2025-09-30 14:26:52
-- CAUTION: Review carefully before executing!

USE crypto_prices;

-- DEFINITELY UNUSED TABLES (Safe to drop)
-- collection_monitoring: Very small table (12 rows, 0.05 MB)
DROP TABLE IF EXISTS `collection_monitoring`;

-- crypto_metadata: Very small table (34 rows, 0.11 MB)
DROP TABLE IF EXISTS `crypto_metadata`;

-- daily_regime_summary: Empty table (0 rows)
DROP TABLE IF EXISTS `daily_regime_summary`;

-- monitoring_alerts: Very small table (17 rows, 0.05 MB)
DROP TABLE IF EXISTS `monitoring_alerts`;

-- sentiment_data: Empty table (0 rows)
DROP TABLE IF EXISTS `sentiment_data`;

-- social_media_posts: Empty table (0 rows)
DROP TABLE IF EXISTS `social_media_posts`;

-- social_platform_stats: Empty table (0 rows)
DROP TABLE IF EXISTS `social_platform_stats`;

-- trading_engine_v2_summary: Empty table (0 rows)
DROP TABLE IF EXISTS `trading_engine_v2_summary`;

-- POTENTIALLY UNUSED TABLES (Review before uncommenting)
-- assets_archived: No recent data and small size (315 rows, 0.03 MB)
-- DROP TABLE IF EXISTS `assets_archived`;

-- macro_indicators: No recent data and small size (48816 rows, 8.06 MB)
-- DROP TABLE IF EXISTS `macro_indicators`;

