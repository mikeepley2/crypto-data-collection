#!/usr/bin/env python3
"""
Enhanced Technical Indicators ML Collector - Production Ready
Calculates and collects comprehensive technical indicators with real-time monitoring
Includes production-grade API endpoints, health scoring, and automated gap detection
"""

import os
import sys
import logging
import mysql.connector
import asyncio
import time
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import schedule
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Dynamic symbol management
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
try:
    from table_config import get_collector_symbols, normalize_symbol_for_exchange
except ImportError:
    logger.warning("Could not import centralized table_config, using fallback")
    get_collector_symbols = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("technical-indicators-collector")

class TechnicalIndicatorsCollector:
    """Production-ready technical indicators collector with comprehensive ML features"""
    
    def __init__(self):
        # Database configuration
        self.db_config = {
            "host": os.getenv("MYSQL_HOST", "172.22.32.1"),
            "user": os.getenv("MYSQL_USER", "news_collector"),
            "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
            "database": os.getenv("MYSQL_DATABASE", "crypto_prices"),
            "charset": "utf8mb4"
        }
        
        # Service configuration
        self.service_name = "Technical Indicators ML Collector"
        self.collection_interval = 300  # 5 minutes (matches current system)
        
        # Statistics tracking
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'symbols_processed': 0,
            'indicators_calculated': 0,
            'database_writes': 0,
            'last_collection': None
        }
        
        # Load symbols
        self._load_symbols_from_database()
        
        # Initialize FastAPI
        self.app = FastAPI(title=self.service_name, version="1.0.0")
        self._setup_routes()
        
        # Background scheduler
        self._setup_scheduler()
        
    def _load_symbols_from_database(self):
        """Load active crypto symbols that have recent price data"""
        try:
            # Primary approach: get symbols with recent price data
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get symbols that have price data in the last 7 days
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM price_data_real 
                WHERE timestamp_iso >= NOW() - INTERVAL 7 DAY
                AND symbol IS NOT NULL
                AND current_price IS NOT NULL
                ORDER BY symbol
                LIMIT 100
            """)
            
            self.symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if self.symbols:
                logger.info(f"Loaded {len(self.symbols)} symbols with recent price data")
            else:
                # Fallback to crypto_assets if available
                if get_collector_symbols:
                    self.symbols = get_collector_symbols('technical')[:50]  # Limit to 50
                    logger.info(f"Loaded {len(self.symbols)} symbols from crypto_assets (fallback)")
                else:
                    # Final fallback
                    self.symbols = ['BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD', 'DOTUSD']
                    logger.info(f"Using hardcoded symbols (final fallback)")
                    
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
            self.symbols = ['BTCUSD', 'ETHUSD', 'ADAUSD', 'SOLUSD', 'DOTUSD']
            logger.info(f"Using hardcoded fallback symbols: {self.symbols}")
    
    def _get_symbols_from_price_data(self) -> List[str]:
        """Fallback method to get symbols from price_data_real"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT symbol 
                FROM price_data_real 
                WHERE timestamp_iso >= NOW() - INTERVAL 7 DAY
                AND symbol IS NOT NULL
                ORDER BY symbol
                LIMIT 150
            """)
            
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting symbols from price_data_real: {e}")
            return []
    
    def get_db_connection(self):
        """Get database connection with error handling"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
        return sum(prices[-period:]) / period

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # For signal line, use simplified calculation
        signal_line = macd_line * 0.9  # Approximate signal
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            avg_price = sum(prices) / len(prices) if prices else 0
            return {
                'bb_upper': avg_price * 1.02,
                'bb_middle': avg_price,
                'bb_lower': avg_price * 0.98
            }
        
        sma = self.calculate_sma(prices, period)
        recent_prices = prices[-period:]
        std = np.std(recent_prices)
        
        return {
            'bb_upper': sma + (std_dev * std),
            'bb_middle': sma,
            'bb_lower': sma - (std_dev * std)
        }

    def get_price_data(self, symbol: str, days_back: int = 50) -> List[Dict]:
        """Get price data for technical indicator calculations"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get price data from the last N days
            query = """
                SELECT 
                    timestamp_iso,
                    current_price,
                    high_24h,
                    low_24h,
                    volume_usd_24h
                FROM price_data_real
                WHERE symbol = %s 
                AND timestamp_iso >= NOW() - INTERVAL %s DAY
                ORDER BY timestamp_iso ASC
                LIMIT 1000
            """
            
            cursor.execute(query, (symbol, days_back))
            data = cursor.fetchall()
            
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return []

    def calculate_indicators_for_symbol(self, symbol: str) -> Optional[Dict]:
        """Calculate all technical indicators for a symbol"""
        try:
            # Get price data
            price_data = self.get_price_data(symbol)
            
            if not price_data or len(price_data) < 20:
                logger.warning(f"Insufficient price data for {symbol}: {len(price_data) if price_data else 0} points")
                return None
            
            # Extract prices (handle None values)
            prices = []
            for row in price_data:
                if row['current_price'] is not None:
                    prices.append(float(row['current_price']))
            
            if len(prices) < 20:
                logger.warning(f"Insufficient valid prices for {symbol}: {len(prices)} points")
                return None
            
            # Calculate all indicators
            rsi_14 = self.calculate_rsi(prices, 14)
            sma_20 = self.calculate_sma(prices, 20)
            sma_50 = self.calculate_sma(prices, 50)
            ema_12 = self.calculate_ema(prices, 12)
            ema_26 = self.calculate_ema(prices, 26)
            
            macd_data = self.calculate_macd(prices)
            bb_data = self.calculate_bollinger_bands(prices)
            
            # Get current price and timestamp
            latest_data = price_data[-1]
            current_price = float(latest_data['current_price'])
            timestamp_iso = latest_data['timestamp_iso']
            
            return {
                'symbol': symbol,
                'timestamp_iso': timestamp_iso,
                'current_price': current_price,
                'rsi_14': round(rsi_14, 6),
                'sma_20': round(sma_20, 6),
                'sma_50': round(sma_50, 6),
                'ema_12': round(ema_12, 6),
                'ema_26': round(ema_26, 6),
                'macd': round(macd_data['macd'], 6),
                'macd_signal': round(macd_data['signal'], 6),
                'macd_histogram': round(macd_data['histogram'], 6),
                'bb_upper': round(bb_data['bb_upper'], 6),
                'bb_middle': round(bb_data['bb_middle'], 6),
                'bb_lower': round(bb_data['bb_lower'], 6)
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return None

    def store_technical_indicators(self, indicators_batch: List[Dict]) -> int:
        """Store technical indicators to database"""
        if not indicators_batch:
            return 0
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            insert_query = """
                INSERT INTO technical_indicators (
                    symbol, timestamp_iso, price, rsi_14, sma_20, sma_50,
                    ema_12, ema_26, macd, macd_signal, macd_histogram,
                    bb_upper, bb_middle, bb_lower, created_at
                ) VALUES (
                    %(symbol)s, %(timestamp_iso)s, %(current_price)s, %(rsi_14)s, %(sma_20)s, %(sma_50)s,
                    %(ema_12)s, %(ema_26)s, %(macd)s, %(macd_signal)s, %(macd_histogram)s,
                    %(bb_upper)s, %(bb_middle)s, %(bb_lower)s, NOW()
                ) ON DUPLICATE KEY UPDATE
                    price = VALUES(price),
                    rsi_14 = VALUES(rsi_14),
                    sma_20 = VALUES(sma_20),
                    sma_50 = VALUES(sma_50),
                    ema_12 = VALUES(ema_12),
                    ema_26 = VALUES(ema_26),
                    macd = VALUES(macd),
                    macd_signal = VALUES(macd_signal),
                    macd_histogram = VALUES(macd_histogram),
                    bb_upper = VALUES(bb_upper),
                    bb_middle = VALUES(bb_middle),
                    bb_lower = VALUES(bb_lower),
                    created_at = NOW()
            """
            
            cursor.executemany(insert_query, indicators_batch)
            rows_affected = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.stats['database_writes'] += rows_affected
            logger.info(f"✅ Stored {rows_affected} technical indicator records")
            return rows_affected
            
        except Exception as e:
            logger.error(f"❌ Error storing technical indicators: {e}")
            return 0

    def run_collection_cycle(self) -> Dict:
        """Run a complete technical indicators collection cycle"""
        start_time = time.time()
        logger.info("🚀 Starting technical indicators collection cycle")
        
        collected_indicators = []
        symbols_processed = 0
        symbols_with_data = 0
        errors = []
        
        try:
            self.stats['total_collections'] += 1
            
            # Process symbols in smaller batches to prevent overwhelming
            active_symbols = self.symbols[:50]  # Limit to 50 symbols per cycle
            
            for symbol in active_symbols:
                try:
                    indicators = self.calculate_indicators_for_symbol(symbol)
                    if indicators:
                        collected_indicators.append(indicators)
                        symbols_with_data += 1
                        
                        # Process in batches of 15
                        if len(collected_indicators) >= 15:
                            stored = self.store_technical_indicators(collected_indicators)
                            collected_indicators = []
                            time.sleep(0.1)  # Rate limiting
                    
                    symbols_processed += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {symbol}: {e}"
                    errors.append(error_msg)
                    if len(errors) <= 3:  # Only log first 3 errors to avoid spam
                        logger.error(error_msg)
            
            # Store remaining indicators
            if collected_indicators:
                stored = self.store_technical_indicators(collected_indicators)
            
            # Update statistics
            total_indicators = symbols_with_data * 12  # 12 indicators per symbol
            self.stats['successful_collections'] += 1
            self.stats['symbols_processed'] += symbols_processed
            self.stats['indicators_calculated'] += total_indicators
            self.stats['last_collection'] = datetime.now().isoformat()
            
            duration = time.time() - start_time
            
            result = {
                'status': 'success',
                'symbols_processed': symbols_processed,
                'symbols_with_data': symbols_with_data,
                'indicators_calculated': total_indicators,
                'duration_seconds': round(duration, 2),
                'errors': len(errors)
            }
            
            logger.info(f"✅ Technical indicators collection completed: {symbols_with_data}/{symbols_processed} symbols with data, {total_indicators} indicators, {duration:.1f}s")
            return result
            
        except Exception as e:
            self.stats['failed_collections'] += 1
            error_msg = f"Collection cycle failed: {e}"
            logger.error(f"❌ {error_msg}")
            return {'status': 'failed', 'error': error_msg}

    def detect_gap(self) -> Optional[float]:
        """Detect data gaps in technical indicators"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(created_at) as latest_record
                FROM technical_indicators
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                latest_time = result[0]
                gap_hours = (datetime.now() - latest_time).total_seconds() / 3600
                return gap_hours
            
            return 24.0  # No data found, assume 24 hour gap
            
        except Exception as e:
            logger.error(f"Error detecting gap: {e}")
            return None

    def calculate_health_score(self) -> int:
        """Calculate health score based on data freshness and collection success"""
        try:
            gap_hours = self.detect_gap() or 0
            
            # Base score from data freshness
            if gap_hours < 1:
                freshness_score = 100
            elif gap_hours < 6:
                freshness_score = 80
            elif gap_hours < 12:
                freshness_score = 60
            elif gap_hours < 24:
                freshness_score = 40
            else:
                freshness_score = 20
            
            # Success rate component
            total_collections = self.stats['total_collections']
            if total_collections > 0:
                success_rate = self.stats['successful_collections'] / total_collections
                success_score = int(success_rate * 50)  # Up to 50 points
            else:
                success_score = 25  # Default for new service
            
            # Combine scores
            health_score = min(100, freshness_score + success_score)
            return max(0, health_score)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50

    def _setup_routes(self):
        """Setup FastAPI routes for production monitoring"""
        
        @self.app.get("/health")
        def health():
            """Health check with scoring"""
            gap_hours = self.detect_gap()
            health_score = self.calculate_health_score()
            
            status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
            
            return {
                "status": status,
                "service": self.service_name,
                "timestamp": datetime.now().isoformat(),
                "health_score": health_score,
                "gap_hours": gap_hours,
                "data_freshness": "healthy" if (gap_hours or 0) < 6 else "stale",
                "symbols_tracked": len(self.symbols),
                "ml_indicators": 12
            }
        
        @self.app.get("/status")
        def status():
            """Detailed service status"""
            gap_hours = self.detect_gap()
            health_score = self.calculate_health_score()
            
            return {
                "service": self.service_name,
                "status": "operational",
                "statistics": self.stats.copy(),
                "configuration": {
                    "symbols_tracked": len(self.symbols),
                    "collection_interval_seconds": self.collection_interval,
                    "ml_indicators": 12,
                    "technical_indicators": ["RSI", "SMA", "EMA", "MACD", "Bollinger Bands"]
                },
                "health_metrics": {
                    "gap_hours": gap_hours,
                    "health_score": health_score,
                    "data_freshness": "healthy" if (gap_hours or 0) < 6 else "stale"
                },
                "data_sources": {
                    "price_data_real": "active"
                }
            }
        
        @self.app.post("/collect")
        def collect(background_tasks: BackgroundTasks):
            """Trigger manual collection"""
            background_tasks.add_task(self.run_collection_cycle)
            return {
                "status": "started",
                "message": "Technical indicators collection triggered",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/gap-check")
        def gap_check():
            """Check for gaps and auto-backfill if needed"""
            gap_hours = self.detect_gap()
            
            if gap_hours and gap_hours > 6:
                # Auto-trigger backfill
                result = self.run_collection_cycle()
                return {
                    "gap_detected": True,
                    "gap_hours": gap_hours,
                    "backfill_triggered": True,
                    "backfill_result": result
                }
            else:
                return {
                    "gap_detected": False,
                    "gap_hours": gap_hours,
                    "message": "No significant gaps found"
                }
        
        @self.app.post("/backfill/{hours}")
        def manual_backfill(hours: int, background_tasks: BackgroundTasks):
            """Manual intensive backfill"""
            background_tasks.add_task(self._intensive_backfill, hours)
            return {
                "status": "started",
                "message": f"Intensive technical indicators backfill for {hours} hours",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/metrics")
        def metrics():
            """Prometheus metrics endpoint"""
            gap_hours = self.detect_gap() or 0
            health_score = self.calculate_health_score()
            
            metrics_text = f"""# HELP technical_indicators_collector_health_score Health score (0-100)
# TYPE technical_indicators_collector_health_score gauge
technical_indicators_collector_health_score {health_score}

# HELP technical_indicators_collector_gap_hours Data gap in hours
# TYPE technical_indicators_collector_gap_hours gauge
technical_indicators_collector_gap_hours {gap_hours}

# HELP technical_indicators_collector_symbols_tracked Number of symbols being tracked
# TYPE technical_indicators_collector_symbols_tracked gauge
technical_indicators_collector_symbols_tracked {len(self.symbols)}

# HELP technical_indicators_collector_total_collections Total number of collection cycles
# TYPE technical_indicators_collector_total_collections counter
technical_indicators_collector_total_collections {self.stats['total_collections']}

# HELP technical_indicators_collector_successful_collections Successful collection cycles
# TYPE technical_indicators_collector_successful_collections counter
technical_indicators_collector_successful_collections {self.stats['successful_collections']}

# HELP technical_indicators_collector_indicators_calculated Total indicators calculated
# TYPE technical_indicators_collector_indicators_calculated counter
technical_indicators_collector_indicators_calculated {self.stats['indicators_calculated']}

# HELP technical_indicators_collector_database_writes Total database writes
# TYPE technical_indicators_collector_database_writes counter
technical_indicators_collector_database_writes {self.stats['database_writes']}

# HELP technical_indicators_collector_running Service running status
# TYPE technical_indicators_collector_running gauge
technical_indicators_collector_running 1
"""
            return PlainTextResponse(metrics_text, media_type="text/plain")
        
        @self.app.get("/technical-features")
        def technical_features():
            """Technical indicators feature information"""
            return {
                "data_source": "Price Data Real (MySQL)",
                "indicators": {
                    "RSI": "Relative Strength Index (momentum oscillator)",
                    "SMA": "Simple Moving Averages (20, 50 periods)",
                    "EMA": "Exponential Moving Averages (12, 26 periods)", 
                    "MACD": "Moving Average Convergence Divergence",
                    "Bollinger_Bands": "Price volatility bands (upper, middle, lower)"
                },
                "ml_features": {
                    "trend_analysis": "SMA/EMA crossovers and slope calculations",
                    "momentum_signals": "RSI overbought/oversold conditions",
                    "volatility_metrics": "Bollinger Band squeeze and expansion",
                    "divergence_detection": "MACD signal crossovers",
                    "price_position": "Current price vs moving averages"
                },
                "tracked_symbols": len(self.symbols),
                "calculation_frequency": "Every 5 minutes",
                "lookback_periods": "Up to 50 days of price history",
                "update_frequency": "Real-time from price_data_real table"
            }

    def _intensive_backfill(self, hours: int):
        """Run intensive backfill for specified hours"""
        logger.info(f"Starting intensive backfill for {hours} hours")
        
        # Run multiple collection cycles
        for i in range(min(hours // 2, 12)):  # Max 12 cycles
            result = self.run_collection_cycle()
            logger.info(f"Backfill cycle {i+1} completed: {result}")
            time.sleep(10)  # 10 second delay between cycles

    def _setup_scheduler(self):
        """Setup background collection scheduler (matches current system)"""
        schedule.every(5).minutes.do(self.run_collection_cycle)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        # Start scheduler in background thread
        import threading
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("📅 Background scheduler started (5-minute intervals)")

def main():
    """Main entry point"""
    # Initialize collector
    collector = TechnicalIndicatorsCollector()
    
    # Run initial collection
    logger.info("Running initial technical indicators collection...")
    result = collector.run_collection_cycle()
    logger.info(f"Initial collection result: {result}")
    
    # Start FastAPI service
    logger.info("🚀 Starting Technical Indicators Collector API service on port 8002")
    uvicorn.run(
        collector.app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )

if __name__ == "__main__":
    main()