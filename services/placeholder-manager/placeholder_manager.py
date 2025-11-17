#!/usr/bin/env python3
"""
Centralized Placeholder Manager Service
Manages placeholder records across all data collectors for comprehensive completeness tracking
"""

import os
import logging
import time
import pymysql
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import schedule
import asyncio
import uvicorn

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("placeholder-manager")


class CentralizedPlaceholderManager:
    """Centralized service for managing placeholder records across all collectors"""
    
    def __init__(self):
        self.service_name = "placeholder-manager"
        self.version = "1.0.0"
        
        # Database configuration
        self.db_config = {
            'host': os.getenv("DB_HOST", "127.0.0.1"),
            'user': os.getenv("DB_USER", "news_collector"),
            'password': os.getenv("DB_PASSWORD", "99Rules!"),
            'database': os.getenv("DB_NAME", "crypto_prices"),
            'charset': 'utf8mb4',
            'autocommit': False
        }
        
        # Configuration
        self.schedule_interval_hours = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "1"))
        self.enable_placeholders = os.getenv("ENABLE_PLACEHOLDERS", "true").lower() == "true"
        
        # Comprehensive collector configurations for ALL data types
        self.collector_configs = {
            'macro': {
                'table': 'macro_economic_data',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily collection schedule
                'indicators': ['VIX', 'DXY', 'FEDFUNDS', 'DGS10', 'DGS2', 'UNRATE', 'CPIAUCSL', 'GDP'],
                'active': True,
                'priority': 8
            },
            'technical': {
                'table': 'technical_indicators',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Changed to daily for efficiency
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 50",
                'active': True,
                'priority': 7
            },
            'onchain_primary': {
                'table': 'crypto_onchain_data',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily collection schedule
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 50",
                'active': True,
                'priority': 6
            },
            'trading_signals': {
                'table': 'trading_signals',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily signals
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 50",
                'active': True,
                'priority': 7
            },
            'enhanced_trading_signals': {
                'table': 'enhanced_trading_signals',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily enhanced signals
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 50",
                'active': False,  # Disabled due to schema issues
                'priority': 8
            },
            'ohlc': {
                'table': 'ohlc_data',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily OHLC for historical
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 50",
                'active': True,
                'priority': 9
            },
            'derivatives': {
                'table': 'crypto_derivatives_ml',
                'start_date': '2023-01-01',
                'frequency': 'daily',  # Daily derivatives data
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 20",
                'active': True,
                'priority': 6
            },
            'onchain_secondary': {
                'table': 'onchain_data',
                'start_date': '2023-01-01',
                'frequency': 'daily',
                'symbols_query': "SELECT DISTINCT symbol FROM crypto_assets WHERE is_active = 1 ORDER BY market_cap_rank LIMIT 30",
                'active': False,  # Disabled if table doesn't exist
                'priority': 5
            },
            'sentiment': {
                'table': 'sentiment_analysis_results',
                'start_date': '2023-01-01',
                'frequency': 'hourly',  # Hourly collection schedule
                'symbols_query': "SELECT DISTINCT symbol FROM price_data_real WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY) LIMIT 30",
                'active': False,  # Optional data type
                'priority': 5
            }
        }
        
        # Statistics tracking
        self.stats = {
            'total_placeholders_created': 0,
            'last_run': None,
            'errors': 0,
            'service_start_time': datetime.now()
        }
        
        # FastAPI app for monitoring/control
        self.app = FastAPI(title=f"{self.service_name} API")
        self.setup_routes()
        
        logger.info(f"✅ {self.service_name} v{self.version} initialized")
        logger.info(f"   Schedule interval: {self.schedule_interval_hours} hours")
        logger.info(f"   Placeholders enabled: {self.enable_placeholders}")
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return pymysql.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_symbols_for_collector(self, collector_type: str) -> List[str]:
        """Get symbols for a specific collector type"""
        config = self.collector_configs.get(collector_type)
        if not config or 'symbols_query' not in config:
            return []
        
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute(config['symbols_query'])
            symbols = [row[0] for row in cursor.fetchall()]
            logger.debug(f"Found {len(symbols)} symbols for {collector_type}")
            return symbols
        except Exception as e:
            logger.error(f"Error getting symbols for {collector_type}: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def ensure_macro_placeholders(self, cursor, lookback_days: int = 30) -> int:
        """Ensure macro indicator placeholders exist (recent data only for regular runs)"""
        placeholders_created = 0
        config = self.collector_configs['macro']
        
        if not config.get('active', True):
            return 0
            
        try:
            # For regular runs, only create recent placeholders to avoid performance issues
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback_days)
            
            logger.info(f"   Creating macro placeholders from {start_date} to {end_date} (recent {lookback_days} days)")
            
            current_date = start_date
            while current_date <= end_date:
                for indicator in config['indicators']:
                    try:
                        cursor.execute("""
                            INSERT IGNORE INTO macro_economic_data
                            (indicator_name, timestamp, value, data_source, 
                             data_completeness_percentage, created_at)
                            VALUES (%s, %s, NULL, 'placeholder_manager', 0.0, NOW())
                        """, (indicator, datetime.combine(current_date, datetime.min.time())))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating macro placeholder {indicator} {current_date}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating macro placeholders: {e}")
        
        return placeholders_created
    
    def ensure_technical_placeholders(self, cursor, hours: int) -> int:
        """Ensure technical indicator placeholders exist (daily frequency for efficiency)"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector('technical')
        config = self.collector_configs['technical']
        
        if not symbols or not config.get('active', True):
            return 0
        
        try:
            # Convert hours to days and use daily frequency for efficiency
            days = max(1, hours // 24)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating technical placeholders for {len(symbols)} symbols from {start_date} to {end_date} (daily)")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    try:
                        # Create daily technical indicators at market close time
                        timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=23, minute=59))
                        
                        cursor.execute("""
                            INSERT IGNORE INTO technical_indicators
                            (symbol, timestamp, 
                             rsi_14, sma_20, sma_50, ema_12, ema_26,
                             macd, macd_signal, macd_histogram,
                             bollinger_upper, bollinger_middle, bollinger_lower, stoch_k, stoch_d, atr_14, vwap,
                             data_completeness_percentage, data_source, created_at)
                            VALUES (%s, %s, 
                                   NULL, NULL, NULL, NULL, NULL,
                                   NULL, NULL, NULL, 
                                   NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                                   0.0, 'placeholder_manager', NOW())
                        """, (symbol, timestamp))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating technical placeholder {symbol} {current_date}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating technical placeholders: {e}")
        
        return placeholders_created
    
    def ensure_onchain_placeholders(self, cursor, days: int, collector_name: str = 'onchain_primary') -> int:
        """Ensure onchain data placeholders exist from 2023 to present (daily frequency)"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector(collector_name)
        config = self.collector_configs[collector_name]
        
        if not symbols or not config.get('active', True):
            return 0
        
        try:
            # For efficiency, only create recent placeholders in regular runs
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating {collector_name} placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    try:
                        cursor.execute(f"""
                            INSERT IGNORE INTO {config['table']}
                            (symbol, timestamp, 
                             current_price, total_volume, high_24h, low_24h, price_change_24h,
                             market_cap, market_cap_rank, circulating_supply, total_supply, max_supply,
                             data_completeness_percentage, data_source)
                            VALUES (%s, %s,
                                   NULL, NULL, NULL, NULL, NULL,
                                   NULL, NULL, NULL, NULL, NULL,
                                   0.0, 'placeholder_manager')
                        """, (symbol, datetime.combine(current_date, datetime.min.time())))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating {collector_name} placeholder {symbol} {current_date}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating {collector_name} placeholders: {e}")
        
        return placeholders_created
    
    def ensure_trading_signal_placeholders(self, cursor, days: int, collector_name: str) -> int:
        """Ensure trading signal placeholders exist"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector(collector_name)
        config = self.collector_configs[collector_name]
        
        if not symbols or not config.get('active', True):
            return 0
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating {collector_name} placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    try:
                        timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=9))
                        
                        if collector_name == 'trading_signals':
                            cursor.execute("""
                                INSERT IGNORE INTO trading_signals
                                (symbol, timestamp, signal_type, signal_strength, confidence,
                                 data_completeness_percentage, data_source)
                                VALUES (%s, %s, NULL, NULL, NULL, 0.0, 'placeholder_manager')
                            """, (symbol, timestamp))
                        elif collector_name == 'enhanced_trading_signals':
                            cursor.execute("""
                                INSERT IGNORE INTO enhanced_trading_signals
                                (symbol, timestamp, signal_type, signal_strength, confidence, ml_score,
                                 data_completeness_percentage, data_source)
                                VALUES (%s, %s, NULL, NULL, NULL, NULL, 0.0, 'placeholder_manager')
                            """, (symbol, timestamp))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating {collector_name} placeholder {symbol} {current_date}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating {collector_name} placeholders: {e}")
        
        return placeholders_created
    
    def ensure_ohlc_placeholders(self, cursor, days: int) -> int:
        """Ensure OHLC data placeholders exist (Note: OHLC table is already populated with real data)"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector('ohlc')
        config = self.collector_configs['ohlc']
        
        if not symbols or not config.get('active', True):
            return 0
        
        # Check if OHLC table already has substantial real data
        try:
            cursor.execute("SELECT COUNT(*) FROM ohlc_data WHERE data_source != 'placeholder_manager'")
            real_data_count = cursor.fetchone()[0]
            
            if real_data_count > 100000:  # Table is already well-populated with real data
                logger.info(f"   OHLC table already has {real_data_count:,} real data records - skipping placeholder creation")
                return 0
        except Exception as e:
            logger.debug(f"Error checking OHLC real data: {e}")
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating OHLC placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    try:
                        # Create one OHLC record per day (at market close time)
                        timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=23, minute=59))
                        
                        # Use correct column name: timestamp_iso instead of timestamp
                        cursor.execute("""
                            INSERT IGNORE INTO ohlc_data
                            (symbol, timestamp_iso, open_price, high_price, low_price, close_price, volume,
                             data_completeness_percentage, data_source)
                            VALUES (%s, %s, NULL, NULL, NULL, NULL, NULL, 0.0, 'placeholder_manager')
                        """, (symbol, timestamp))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating OHLC placeholder {symbol} {current_date}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating OHLC placeholders: {e}")
        
        return placeholders_created
    
    def ensure_derivatives_placeholders(self, cursor, days: int) -> int:
        """Ensure derivatives ML placeholders exist"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector('derivatives')
        config = self.collector_configs['derivatives']
        
        if not symbols or not config.get('active', True):
            logger.info(f"   Derivatives: No symbols found or collector inactive")
            return 0
        
        try:
            # Check if derivatives table is empty (needs placeholders)
            cursor.execute("SELECT COUNT(*) FROM crypto_derivatives_ml")
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                logger.info(f"   Derivatives table is empty - creating placeholders for {len(symbols)} symbols")
                # For empty table, create more comprehensive historical coverage
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=max(days, 90))  # At least 90 days for empty table
            else:
                logger.info(f"   Derivatives table has {total_records} records - creating recent placeholders only")
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating derivatives placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    try:
                        timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=16))
                        
                        # Use actual column names from the derivatives table structure
                        cursor.execute("""
                            INSERT IGNORE INTO crypto_derivatives_ml
                            (symbol, timestamp, exchange, funding_rate, predicted_funding_rate,
                             open_interest_usdt, ml_funding_momentum_score, ml_liquidation_risk_score,
                             data_completeness_percentage, data_source)
                            VALUES (%s, %s, 'placeholder', NULL, NULL, NULL, NULL, NULL, 0.0, 'placeholder_manager')
                        """, (symbol, timestamp))
                        
                        if cursor.rowcount > 0:
                            placeholders_created += 1
                            
                    except Exception as e:
                        logger.debug(f"Error creating derivatives placeholder {symbol} {current_date}: {e}")
                
                current_date += timedelta(days=1)
                
                # Commit every 1000 records for large batches
                if placeholders_created % 1000 == 0 and placeholders_created > 0:
                    cursor.connection.commit()
                    logger.info(f"   Derivatives progress: {placeholders_created} placeholders created...")
        
        except Exception as e:
            logger.error(f"Error creating derivatives placeholders: {e}")
        
        return placeholders_created
    
    def ensure_sentiment_placeholders(self, cursor, days: int) -> int:
        """Ensure sentiment analysis placeholders exist"""
        placeholders_created = 0
        symbols = self.get_symbols_for_collector('sentiment')
        
        if not symbols:
            return 0
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"   Creating sentiment placeholders for {len(symbols)} symbols from {start_date} to {end_date}")
            
            current_date = start_date
            while current_date <= end_date:
                for symbol in symbols:
                    # Create hourly placeholders for sentiment data
                    for hour in range(24):
                        try:
                            timestamp = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                            
                            cursor.execute("""
                                INSERT IGNORE INTO sentiment_analysis_results
                                (symbol, timestamp, 
                                 sentiment_score, confidence_level, data_source,
                                 data_completeness_percentage, created_at)
                                VALUES (%s, %s, NULL, NULL, 'placeholder_manager', 0.0, NOW())
                            """, (symbol, timestamp))
                            
                            if cursor.rowcount > 0:
                                placeholders_created += 1
                                
                        except Exception as e:
                            logger.debug(f"Error creating sentiment placeholder {symbol} {timestamp}: {e}")
                
                current_date += timedelta(days=1)
        
        except Exception as e:
            logger.error(f"Error creating sentiment placeholders: {e}")
        
        return placeholders_created
    
    def ensure_comprehensive_placeholders(self) -> Dict[str, int]:
        """Ensure all expected placeholder records exist across all active collectors"""
        if not self.enable_placeholders:
            logger.info("Placeholder creation disabled")
            return {}
        
        logger.info("🔧 Running comprehensive placeholder creation...")
        
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        results = {}
        
        try:
            cursor = conn.cursor()
            
            # Process all active collectors based on priority (higher priority first)
            active_configs = [(name, config) for name, config in self.collector_configs.items() 
                            if config.get('active', True)]
            active_configs.sort(key=lambda x: x[1].get('priority', 5), reverse=True)
            
            for collector_name, config in active_configs:
                try:
                    logger.info(f"   Processing {collector_name} (priority {config.get('priority', 5)})...")
                    
                    if collector_name == 'macro':
                        created = self.ensure_macro_placeholders(cursor, 30)
                    elif collector_name == 'technical':
                        created = self.ensure_technical_placeholders(cursor, 168)  # 7 days in hours
                    elif collector_name.startswith('onchain'):
                        created = self.ensure_onchain_placeholders(cursor, 30, collector_name)
                    elif collector_name.startswith('trading'):
                        created = self.ensure_trading_signal_placeholders(cursor, 30, collector_name)
                    elif collector_name == 'ohlc':
                        created = self.ensure_ohlc_placeholders(cursor, 30)
                    elif collector_name == 'derivatives':
                        created = self.ensure_derivatives_placeholders(cursor, 30)
                    elif collector_name == 'sentiment':
                        created = self.ensure_sentiment_placeholders(cursor, 30)
                    else:
                        logger.warning(f"Unknown collector type: {collector_name}")
                        created = 0
                    
                    results[collector_name] = created
                    
                    if created > 0:
                        logger.info(f"   ✅ {collector_name}: {created} placeholders created")
                    
                except Exception as e:
                    logger.error(f"Error processing {collector_name}: {e}")
                    results[collector_name] = 0
            
            conn.commit()
            
            total_created = sum(results.values())
            self.stats['total_placeholders_created'] += total_created
            self.stats['last_run'] = datetime.now()
            
            logger.info(f"✅ Comprehensive placeholder creation completed:")
            for collector, count in results.items():
                if count > 0:
                    logger.info(f"   {collector}: {count} placeholders")
            logger.info(f"   Total: {total_created} placeholders")
            
            return results
            
        except Exception as e:
            logger.error(f"Error ensuring comprehensive placeholders: {e}")
            self.stats['errors'] += 1
            conn.rollback()
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def get_completeness_summary(self) -> Dict:
        """Get system-wide completeness summary for all data types"""
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            summary = {}
            
            # Process all active collector configurations
            for collector_name, config in self.collector_configs.items():
                if not config.get('active', True):
                    continue
                    
                table = config['table']
                
                try:
                    # Check if table exists
                    cursor.execute(f"SHOW TABLES LIKE '{table}'")
                    if not cursor.fetchone():
                        summary[collector_name] = {'error': 'Table does not exist'}
                        continue
                    
                    # Check if data_completeness_percentage column exists
                    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'data_completeness_percentage'")
                    has_completeness = cursor.fetchone() is not None
                    
                    if not has_completeness:
                        summary[collector_name] = {'error': 'Missing completeness column'}
                        continue
                    
                    # Determine appropriate timestamp column and time range
                    timestamp_col = 'timestamp'
                    time_range = 'INTERVAL 30 DAY'
                    
                    if collector_name == 'macro':
                        timestamp_col = 'timestamp'
                        time_range = 'INTERVAL 30 DAY'
                    elif collector_name in ['technical', 'sentiment']:
                        timestamp_col = 'timestamp'
                        time_range = 'INTERVAL 7 DAY'
                    elif collector_name.startswith('onchain'):
                        timestamp_col = 'timestamp'
                        time_range = 'INTERVAL 30 DAY'
                    elif collector_name.startswith('trading') or collector_name in ['ohlc', 'derivatives']:
                        timestamp_col = 'timestamp'
                        time_range = 'INTERVAL 30 DAY'
                    
                    # Get completeness summary
                    cursor.execute(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
                            AVG(COALESCE(data_completeness_percentage, 0)) as avg_completeness,
                            MIN({timestamp_col}) as earliest_record,
                            MAX({timestamp_col}) as latest_record
                        FROM {table}
                        WHERE {timestamp_col} >= DATE_SUB(NOW(), {time_range})
                    """)
                    summary[collector_name] = cursor.fetchone()
                    
                except Exception as e:
                    logger.debug(f"Error getting summary for {collector_name}: {e}")
                    summary[collector_name] = {'error': str(e)}
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting completeness summary: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def detect_and_fill_gaps(self) -> Dict[str, int]:
        """Detect missing placeholder records and create them"""
        logger.info("🔍 Detecting and filling placeholder gaps...")
        
        # This is essentially the same as comprehensive placeholder creation
        # but could be enhanced with more sophisticated gap detection logic
        return self.ensure_comprehensive_placeholders()
    
    def cleanup_old_placeholders(self, days_old: int = 30) -> int:
        """Clean up old placeholder records that remain unfilled"""
        conn = self.get_db_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            total_cleaned = 0
            
            # Define cleanup queries for each table
            cleanup_queries = [
                ("macro_indicators", "indicator_date"),
                ("technical_indicators", "DATE(timestamp)"),
                ("crypto_onchain_data", "data_date"),
                ("sentiment_analysis_results", "DATE(timestamp)")
            ]
            
            for table, date_field in cleanup_queries:
                try:
                    cursor.execute(f"""
                        DELETE FROM {table} 
                        WHERE data_completeness_percentage = 0 
                        AND data_source LIKE '%placeholder%'
                        AND {date_field} < DATE_SUB(CURDATE(), INTERVAL %s DAY)
                    """, (days_old,))
                    
                    cleaned = cursor.rowcount
                    total_cleaned += cleaned
                    
                    if cleaned > 0:
                        logger.info(f"Cleaned {cleaned} old placeholders from {table}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning {table}: {e}")
            
            conn.commit()
            logger.info(f"✅ Cleaned {total_cleaned} total old placeholder records")
            return total_cleaned
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def setup_routes(self):
        """Setup FastAPI routes for monitoring and control"""
        
        @self.app.get("/health")
        def health():
            """Kubernetes health check endpoint"""
            return {"status": "ok", "service": self.service_name}
        
        @self.app.get("/status")
        def status():
            """Detailed service status"""
            summary = self.get_completeness_summary()
            
            return {
                "service": self.service_name,
                "version": self.version,
                "stats": self.stats,
                "config": self.collector_configs,
                "completeness_summary": summary,
                "health": "healthy" if self.stats['errors'] < 10 else "degraded"
            }
        
        @self.app.post("/create-placeholders")
        def create_placeholders(background_tasks: BackgroundTasks):
            """Manually trigger comprehensive placeholder creation"""
            background_tasks.add_task(self.ensure_comprehensive_placeholders)
            return {"status": "started", "message": "Placeholder creation initiated"}
        
        @self.app.post("/fill-gaps")
        def fill_gaps(background_tasks: BackgroundTasks):
            """Manually trigger gap detection and filling"""
            background_tasks.add_task(self.detect_and_fill_gaps)
            return {"status": "started", "message": "Gap filling initiated"}
        
        @self.app.post("/cleanup/{days}")
        def cleanup_placeholders(days: int, background_tasks: BackgroundTasks):
            """Manually trigger cleanup of old placeholders"""
            if days < 7:
                return {"error": "Minimum cleanup age is 7 days"}
            
            background_tasks.add_task(self.cleanup_old_placeholders, days)
            return {"status": "started", "message": f"Cleanup initiated for placeholders older than {days} days"}
        
        @self.app.get("/completeness")
        def get_completeness():
            """Get current completeness summary"""
            return self.get_completeness_summary()
        
        @self.app.get("/metrics")
        def prometheus_metrics():
            """Prometheus metrics endpoint"""
            summary = self.get_completeness_summary()
            
            metrics = f"""# HELP placeholder_manager_total_created Total placeholder records created
# TYPE placeholder_manager_total_created counter
placeholder_manager_total_created {self.stats['total_placeholders_created']}

# HELP placeholder_manager_errors Total errors encountered
# TYPE placeholder_manager_errors counter
placeholder_manager_errors {self.stats['errors']}

# HELP placeholder_manager_running Service running status
# TYPE placeholder_manager_running gauge
placeholder_manager_running 1

"""
            
            # Add completeness metrics for each collector
            for collector, data in summary.items():
                if data and 'avg_completeness' in data:
                    metrics += f"""# HELP {collector}_avg_completeness Average completeness percentage
# TYPE {collector}_avg_completeness gauge
{collector}_avg_completeness {data['avg_completeness'] or 0:.1f}

"""
            
            return JSONResponse(content=metrics, media_type="text/plain")
    
    def run_scheduler(self):
        """Run the scheduled placeholder management process"""
        logger.info(f"🕐 Starting placeholder manager scheduler")
        logger.info(f"   Schedule interval: {self.schedule_interval_hours} hours")
        
        # Schedule comprehensive placeholder creation
        schedule.every(self.schedule_interval_hours).hours.do(self.ensure_comprehensive_placeholders)
        
        # Schedule daily cleanup (at 2 AM)
        schedule.every().day.at("02:00").do(self.cleanup_old_placeholders, 30)
        
        # Run initial placeholder creation
        self.ensure_comprehensive_placeholders()
        
        # Run scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(300)  # Check every 5 minutes
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(600)  # Wait 10 minutes on errors


async def run_api_server(manager: CentralizedPlaceholderManager):
    """Run the FastAPI server"""
    config = uvicorn.Config(
        manager.app,
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8080")),
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main execution function"""
    manager = CentralizedPlaceholderManager()
    
    mode = os.getenv("MODE", "scheduler")
    
    if mode == "api":
        # Run as API server only
        logger.info("Running in API server mode")
        await run_api_server(manager)
    elif mode == "once":
        # Run placeholder creation once and exit
        logger.info("Running placeholder creation once")
        results = manager.ensure_comprehensive_placeholders()
        print(f"Placeholder creation completed: {results}")
    else:
        # Run scheduler with API server
        logger.info("Running in scheduler mode")
        import threading
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=manager.run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Run API server
        await run_api_server(manager)


if __name__ == "__main__":
    asyncio.run(main())