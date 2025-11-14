#!/usr/bin/env python3
"""
Enhanced Technical Calculator - Template Compliant Version
Migrated from legacy implementation to standardized collector template
"""

import asyncio
import aiohttp
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import mysql.connector
import numpy as np
import pandas as pd
import math

from base_collector_template import (
    BaseCollector, CollectorConfig, DataQualityReport, AlertRequest
)

class TechnicalCalculatorConfig(CollectorConfig):
    """Extended configuration for technical calculator"""
    
    def __init__(self, *args, **kwargs):
        # Remove technical calculator specific args before calling parent
        self.batch_processing_size = kwargs.pop('batch_processing_size', 10)
        self.price_data_limit = kwargs.pop('price_data_limit', 200)
        self.min_periods_for_indicators = kwargs.pop('min_periods_for_indicators', 20)
        
        # Call parent constructor with remaining args
        super().__init__(*args, **kwargs)
        
        # Technical indicator configuration
        self.indicators_to_calculate = [
            'sma_20', 'sma_50', 'sma_200',
            'ema_12', 'ema_26',
            'rsi_14', 'rsi_7',
            'macd', 'bollinger_bands',
            'stochastic_k', 'stochastic_d'
        ]
        
        # Calculation periods
        self.sma_periods = [20, 50, 200]
        self.ema_periods = [12, 26]
        self.rsi_periods = [14, 7]
        self.bollinger_period = 20
        self.bollinger_std = 2
        self.stochastic_k_period = 14
        self.stochastic_d_period = 3

    @classmethod
    def from_env(cls) -> 'TechnicalCalculatorConfig':
        """Load configuration from environment variables"""
        # Get base config first
        config = CollectorConfig.from_env()
        
        # Create technical config with base config attributes
        tech_config = cls(
            # Database
            mysql_host=config.mysql_host,
            mysql_port=config.mysql_port,
            mysql_user=config.mysql_user,
            mysql_password=config.mysql_password,
            mysql_database=config.mysql_database,
            
            # Collection
            collection_interval=config.collection_interval,
            backfill_batch_size=config.backfill_batch_size,
            max_retry_attempts=config.max_retry_attempts,
            api_timeout=config.api_timeout,
            api_rate_limit=config.api_rate_limit,
            
            # Dates
            collector_beginning_date=config.collector_beginning_date,
            backfill_lookback_days=config.backfill_lookback_days,
            
            # Logging
            log_level=config.log_level,
            log_format=config.log_format,
            enable_audit_logging=config.enable_audit_logging,
            
            # Service
            service_name="enhanced-technical-calculator",  # Override for this service
            service_version=config.service_version,
            health_check_interval=config.health_check_interval,
            
            # Rate limiting and circuit breaker
            enable_rate_limiting=config.enable_rate_limiting,
            api_rate_limit_per_minute=config.api_rate_limit_per_minute,
            circuit_breaker_failure_threshold=config.circuit_breaker_failure_threshold,
            circuit_breaker_timeout=config.circuit_breaker_timeout,
            
            # Data validation
            enable_data_validation=config.enable_data_validation,
            enable_duplicate_detection=config.enable_duplicate_detection,
            data_retention_days=config.data_retention_days,
            
            # Performance
            connection_pool_size=config.connection_pool_size,
            query_timeout=config.query_timeout,
            batch_commit_size=config.batch_commit_size,
            
            # Alerting
            enable_alerting=config.enable_alerting,
            alert_webhook_url=config.alert_webhook_url,
            alert_error_threshold=config.alert_error_threshold,
            
            # Technical calculator specific
            batch_processing_size=int(os.getenv('TECH_BATCH_SIZE', '10')),
            price_data_limit=int(os.getenv('TECH_PRICE_DATA_LIMIT', '200')),
            min_periods_for_indicators=int(os.getenv('TECH_MIN_PERIODS', '20'))
        )
        
        return tech_config

class EnhancedTechnicalCalculator(BaseCollector):
    """
    Enhanced Technical Calculator implementing the standardized collector template
    Calculates various technical indicators for cryptocurrency price data
    """
    
    def __init__(self):
        config = TechnicalCalculatorConfig.from_env()
        super().__init__(config)

    async def collect_data(self) -> int:
        """
        Calculate technical indicators for all active symbols
        Returns number of symbols processed
        """
        self.logger.info("technical_calculation_started")
        
        # Get active symbols
        symbols = await self._get_active_symbols()
        
        if not symbols:
            self.logger.warning("no_active_symbols_found")
            return 0
        
        processed_count = 0
        batch_size = self.config.batch_processing_size
        
        # Process symbols in batches
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            
            for symbol in batch_symbols:
                try:
                    # Rate limiting
                    if self.rate_limiter:
                        await self.rate_limiter.wait_for_token()
                    
                    # Calculate indicators for symbol
                    success = await self._calculate_symbol_indicators(symbol)
                    if success:
                        processed_count += 1
                        self.metrics['records_processed_total'].labels(operation='technical_calc').inc()
                    
                except Exception as e:
                    self.logger.error("symbol_calculation_error", 
                                     symbol=symbol, error=str(e))
                    self.collection_errors += 1
                    
                    # Send alert if too many errors
                    if (self.config.enable_alerting 
                        and self.collection_errors >= self.config.alert_error_threshold):
                        await self._send_alert(AlertRequest(
                            alert_type="technical_calculation_errors",
                            severity="warning",
                            message=f"Multiple technical calculation failures: {symbol}",
                            service=self.config.service_name,
                            additional_data={"symbol": symbol, "error": str(e)}
                        ))
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        self.logger.info("technical_calculation_completed", 
                        processed=processed_count, total_symbols=len(symbols))
        return processed_count

    async def _get_active_symbols(self) -> List[str]:
        """Get list of active cryptocurrency symbols"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM crypto_assets 
                    WHERE status = 'active' 
                    ORDER BY symbol
                """)
                
                symbols = [row[0] for row in cursor.fetchall()]
                self.logger.info("active_symbols_loaded", count=len(symbols))
                return symbols
                
        except Exception as e:
            self.logger.error("failed_to_load_symbols", error=str(e))
            # Fallback to common symbols
            fallback_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX', 'LINK']
            self.logger.info("using_fallback_symbols", symbols=fallback_symbols)
            return fallback_symbols

    async def _calculate_symbol_indicators(self, symbol: str) -> bool:
        """Calculate all technical indicators for a single symbol"""
        
        try:
            # Get price data
            price_data = await self._get_price_data(symbol)
            
            if not price_data or len(price_data) < self.config.min_periods_for_indicators:
                self.logger.warning("insufficient_price_data", 
                                  symbol=symbol, data_points=len(price_data) if price_data else 0)
                return False
            
            # Data validation if enabled
            if self.config.enable_data_validation:
                validation_result = await self._validate_data({
                    "symbol": symbol,
                    "data_points": len(price_data),
                    "latest_timestamp": price_data[0]["timestamp"] if price_data else None
                })
                if not validation_result["is_valid"]:
                    self.logger.warning("price_data_validation_failed",
                                      symbol=symbol, 
                                      errors=validation_result["errors"])
                    return False
            
            # Calculate all indicators
            indicators = await self._calculate_all_indicators(symbol, price_data)
            
            # Store indicators in database
            success = await self._store_indicators(symbol, indicators)
            
            self.logger.debug("symbol_indicators_calculated", 
                            symbol=symbol, indicators_count=len(indicators))
            return success
            
        except Exception as e:
            self.logger.error("symbol_indicator_calculation_error", 
                             symbol=symbol, error=str(e))
            raise

    async def _get_price_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Get recent price data for a symbol"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT timestamp_iso, open, high, low, close, volume
                    FROM price_data_real 
                    WHERE symbol = %s 
                    AND timestamp_iso >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    ORDER BY timestamp_iso DESC 
                    LIMIT %s
                """, (symbol, self.config.price_data_limit))
                
                price_data = cursor.fetchall()
                
                # Convert to proper data types and sort chronologically
                processed_data = []
                for row in price_data:
                    try:
                        processed_data.append({
                            "timestamp": row["timestamp_iso"],
                            "open": float(row["open"]) if row["open"] else 0.0,
                            "high": float(row["high"]) if row["high"] else 0.0,
                            "low": float(row["low"]) if row["low"] else 0.0,
                            "close": float(row["close"]) if row["close"] else 0.0,
                            "volume": float(row["volume"]) if row["volume"] else 0.0
                        })
                    except (ValueError, TypeError):
                        continue
                
                # Sort chronologically (oldest first) for calculations
                processed_data.reverse()
                
                self.metrics['database_operations_total'].labels(operation='price_data_read', status='success').inc()
                return processed_data
                
        except Exception as e:
            self.logger.error("price_data_retrieval_error", symbol=symbol, error=str(e))
            self.metrics['database_operations_total'].labels(operation='price_data_read', status='error').inc()
            raise

    async def _calculate_all_indicators(self, symbol: str, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate all technical indicators for the given price data"""
        
        # Extract price arrays
        closes = [d["close"] for d in price_data]
        highs = [d["high"] for d in price_data]
        lows = [d["low"] for d in price_data]
        volumes = [d["volume"] for d in price_data]
        
        indicators = {}
        
        try:
            # Simple Moving Averages
            for period in self.config.sma_periods:
                sma = self._calculate_sma(closes, period)
                if sma is not None:
                    indicators[f"sma_{period}"] = sma
            
            # Exponential Moving Averages  
            for period in self.config.ema_periods:
                ema = self._calculate_ema(closes, period)
                if ema is not None:
                    indicators[f"ema_{period}"] = ema
            
            # RSI
            for period in self.config.rsi_periods:
                rsi = self._calculate_rsi(closes, period)
                if rsi is not None:
                    indicators[f"rsi_{period}"] = rsi
            
            # MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(closes)
            if macd_line is not None:
                indicators["macd_line"] = macd_line
                indicators["macd_signal"] = macd_signal
                indicators["macd_histogram"] = macd_histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                closes, self.config.bollinger_period, self.config.bollinger_std
            )
            if bb_middle is not None:
                indicators["bb_upper"] = bb_upper
                indicators["bb_middle"] = bb_middle
                indicators["bb_lower"] = bb_lower
            
            # Stochastic Oscillator
            stoch_k, stoch_d = self._calculate_stochastic(
                highs, lows, closes, 
                self.config.stochastic_k_period, 
                self.config.stochastic_d_period
            )
            if stoch_k is not None:
                indicators["stoch_k"] = stoch_k
                indicators["stoch_d"] = stoch_d
            
            # Add metadata
            indicators["calculated_at"] = datetime.now(timezone.utc)
            indicators["data_points"] = len(price_data)
            indicators["latest_price"] = closes[-1]
            
            return indicators
            
        except Exception as e:
            self.logger.error("indicator_calculation_error", symbol=symbol, error=str(e))
            raise

    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        
        if len(prices) < period:
            return None
        
        return round(sum(prices[-period:]) / period, 6)

    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]  # Start with first price
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return round(ema, 6)

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 4)

    def _calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        
        if len(prices) < slow_period:
            return None, None, None
        
        try:
            ema_fast = self._calculate_ema(prices, fast_period)
            ema_slow = self._calculate_ema(prices, slow_period)
            
            if ema_fast is None or ema_slow is None:
                return None, None, None
            
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line (EMA of MACD line)
            # For simplicity, using a basic average here
            # In production, you'd want to maintain MACD history
            macd_signal = macd_line  # Simplified
            macd_histogram = macd_line - macd_signal
            
            return (
                round(macd_line, 6),
                round(macd_signal, 6),
                round(macd_histogram, 6)
            )
            
        except Exception:
            return None, None, None

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands"""
        
        if len(prices) < period:
            return None, None, None
        
        try:
            # Middle line (SMA)
            middle = self._calculate_sma(prices, period)
            
            if middle is None:
                return None, None, None
            
            # Standard deviation
            recent_prices = prices[-period:]
            variance = sum((p - middle) ** 2 for p in recent_prices) / period
            std = math.sqrt(variance)
            
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            
            return (
                round(upper, 6),
                round(middle, 6),
                round(lower, 6)
            )
            
        except Exception:
            return None, None, None

    def _calculate_stochastic(self, highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Tuple[Optional[float], Optional[float]]:
        """Calculate Stochastic Oscillator"""
        
        if len(closes) < k_period:
            return None, None
        
        try:
            # %K calculation
            recent_highs = highs[-k_period:]
            recent_lows = lows[-k_period:]
            current_close = closes[-1]
            
            highest_high = max(recent_highs)
            lowest_low = min(recent_lows)
            
            if highest_high == lowest_low:
                stoch_k = 50.0  # Avoid division by zero
            else:
                stoch_k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
            
            # %D calculation (simplified as SMA of %K)
            # In production, you'd want to maintain %K history
            stoch_d = stoch_k  # Simplified
            
            return (
                round(stoch_k, 4),
                round(stoch_d, 4)
            )
            
        except Exception:
            return None, None

    async def _store_indicators(self, symbol: str, indicators: Dict[str, Any]) -> bool:
        """Store calculated indicators in database"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare values for insertion
                timestamp = datetime.now(timezone.utc)
                
                # Insert/update technical indicators
                cursor.execute("""
                    INSERT INTO technical_indicators (
                        symbol, timestamp_iso,
                        sma_20, sma_50, sma_200,
                        ema_12, ema_26,
                        rsi_14, rsi_7,
                        macd_line, macd_signal, macd_histogram,
                        bb_upper, bb_middle, bb_lower,
                        stoch_k, stoch_d,
                        latest_price, data_points,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON DUPLICATE KEY UPDATE
                        sma_20 = VALUES(sma_20),
                        sma_50 = VALUES(sma_50),
                        sma_200 = VALUES(sma_200),
                        ema_12 = VALUES(ema_12),
                        ema_26 = VALUES(ema_26),
                        rsi_14 = VALUES(rsi_14),
                        rsi_7 = VALUES(rsi_7),
                        macd_line = VALUES(macd_line),
                        macd_signal = VALUES(macd_signal),
                        macd_histogram = VALUES(macd_histogram),
                        bb_upper = VALUES(bb_upper),
                        bb_middle = VALUES(bb_middle),
                        bb_lower = VALUES(bb_lower),
                        stoch_k = VALUES(stoch_k),
                        stoch_d = VALUES(stoch_d),
                        latest_price = VALUES(latest_price),
                        data_points = VALUES(data_points),
                        updated_at = VALUES(updated_at)
                """, (
                    symbol, timestamp,
                    indicators.get("sma_20"), indicators.get("sma_50"), indicators.get("sma_200"),
                    indicators.get("ema_12"), indicators.get("ema_26"),
                    indicators.get("rsi_14"), indicators.get("rsi_7"),
                    indicators.get("macd_line"), indicators.get("macd_signal"), indicators.get("macd_histogram"),
                    indicators.get("bb_upper"), indicators.get("bb_middle"), indicators.get("bb_lower"),
                    indicators.get("stoch_k"), indicators.get("stoch_d"),
                    indicators.get("latest_price"), indicators.get("data_points"),
                    timestamp, timestamp
                ))
                
                conn.commit()
                self.metrics['database_operations_total'].labels(operation='indicator_insert', status='success').inc()
                
                return True
                
        except Exception as e:
            self.logger.error("indicator_storage_error", symbol=symbol, error=str(e))
            self.metrics['database_operations_total'].labels(operation='indicator_insert', status='error').inc()
            raise

    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """
        Backfill missing technical indicators for historical periods
        """
        
        self.logger.info("technical_backfill_started", periods=len(missing_periods), force=force)
        
        total_processed = 0
        
        try:
            for period in missing_periods:
                symbols = await self._get_active_symbols()
                
                for symbol in symbols:
                    try:
                        if self.rate_limiter:
                            await self.rate_limiter.wait_for_token()
                        
                        # Get historical price data for the period
                        price_data = await self._get_historical_price_data(symbol, period)
                        
                        if price_data and len(price_data) >= self.config.min_periods_for_indicators:
                            indicators = await self._calculate_all_indicators(symbol, price_data)
                            success = await self._store_indicators(symbol, indicators)
                            
                            if success:
                                total_processed += 1
                        
                        await asyncio.sleep(0.1)  # Rate limiting
                        
                    except Exception as e:
                        self.logger.error("backfill_symbol_error", 
                                        symbol=symbol, period=period, error=str(e))
        
        except Exception as e:
            self.logger.error("technical_backfill_error", error=str(e))
            raise
        
        self.logger.info("technical_backfill_completed", processed=total_processed)
        return total_processed

    async def _get_historical_price_data(self, symbol: str, period: Dict) -> List[Dict[str, Any]]:
        """Get historical price data for a specific period"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                if "start_date" in period and "end_date" in period:
                    cursor.execute("""
                        SELECT timestamp_iso, open, high, low, close, volume
                        FROM price_data_real 
                        WHERE symbol = %s 
                        AND timestamp_iso BETWEEN %s AND %s
                        ORDER BY timestamp_iso ASC
                    """, (symbol, period["start_date"], period["end_date"]))
                else:
                    # Single date
                    cursor.execute("""
                        SELECT timestamp_iso, open, high, low, close, volume
                        FROM price_data_real 
                        WHERE symbol = %s 
                        AND DATE(timestamp_iso) = %s
                        ORDER BY timestamp_iso ASC
                    """, (symbol, period.get("date")))
                
                price_data = cursor.fetchall()
                
                # Process data
                processed_data = []
                for row in price_data:
                    try:
                        processed_data.append({
                            "timestamp": row["timestamp_iso"],
                            "open": float(row["open"]) if row["open"] else 0.0,
                            "high": float(row["high"]) if row["high"] else 0.0,
                            "low": float(row["low"]) if row["low"] else 0.0,
                            "close": float(row["close"]) if row["close"] else 0.0,
                            "volume": float(row["volume"]) if row["volume"] else 0.0
                        })
                    except (ValueError, TypeError):
                        continue
                
                return processed_data
                
        except Exception as e:
            self.logger.error("historical_price_data_error", symbol=symbol, error=str(e))
            return []

    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """Get status of technical indicators table"""
        
        try:
            # Get overall statistics
            cursor.execute("""
                SELECT COUNT(*) as total_records,
                       COUNT(DISTINCT symbol) as symbols_count,
                       MAX(updated_at) as last_calculation,
                       MIN(timestamp_iso) as earliest_data,
                       MAX(timestamp_iso) as latest_data
                FROM technical_indicators
            """)
            
            result = cursor.fetchone()
            
            # Get symbols with recent calculations
            cursor.execute("""
                SELECT symbol, COUNT(*) as indicator_count,
                       MAX(updated_at) as last_update
                FROM technical_indicators 
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                GROUP BY symbol
                ORDER BY last_update DESC
                LIMIT 10
            """)
            
            recent_symbols = {row[0]: {"count": row[1], "last_update": row[2]} 
                            for row in cursor.fetchall()}
            
            return {
                "technical_indicators": {
                    "total_records": result[0] if result else 0,
                    "symbols_count": result[1] if result else 0,
                    "last_calculation": result[2] if result and result[2] else None,
                    "earliest_data": result[3] if result and result[3] else None,
                    "latest_data": result[4] if result and result[4] else None,
                    "recent_symbols": recent_symbols
                }
            }
            
        except mysql.connector.Error as e:
            return {"error": str(e)}

    async def _analyze_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Analyze missing technical indicator data
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Find symbols with missing indicators
                if symbols:
                    symbol_condition = "AND symbol IN ({})".format(",".join(["'"+s+"'" for s in symbols]))
                else:
                    symbol_condition = ""
                
                cursor.execute(f"""
                    SELECT symbol, DATE(timestamp_iso) as calc_date,
                           COUNT(*) as indicators_count
                    FROM technical_indicators
                    WHERE timestamp_iso BETWEEN %s AND %s
                    {symbol_condition}
                    GROUP BY symbol, DATE(timestamp_iso)
                    HAVING indicators_count < 10
                    ORDER BY symbol, calc_date
                """, (start_date, end_date))
                
                results = cursor.fetchall()
                
                missing_periods = []
                for symbol, calc_date, indicators_count in results:
                    missing_periods.append({
                        "symbol": symbol,
                        "date": calc_date,
                        "indicators_count": indicators_count,
                        "reason": "incomplete_indicators"
                    })
                
                return missing_periods
                
        except Exception as e:
            self.logger.error("missing_indicators_analysis_error", error=str(e))
            return []

    async def _estimate_backfill_records(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> int:
        """
        Estimate number of indicator records that would be backfilled
        """
        
        try:
            days = (end_date - start_date).days
            symbols_count = len(symbols) if symbols else len(await self._get_active_symbols())
            
            # Estimate: one indicator calculation per symbol per day
            return days * symbols_count
            
        except Exception as e:
            self.logger.error("technical_backfill_estimation_error", error=str(e))
            return 0

    async def _get_required_fields(self) -> List[str]:
        """Get required fields for data validation"""
        return ["symbol", "data_points", "latest_timestamp"]

    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Generate comprehensive data quality report for technical indicators"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Get total symbols that should have indicators
                cursor.execute("SELECT COUNT(DISTINCT symbol) FROM crypto_assets WHERE status = 'active'")
                total_symbols = cursor.fetchone()[0]
                
                # Get symbols with recent indicators
                cursor.execute("""
                    SELECT COUNT(DISTINCT symbol) FROM technical_indicators
                    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                """)
                symbols_with_indicators = cursor.fetchone()[0]
                
                # Get indicators with null values
                cursor.execute("""
                    SELECT COUNT(*) FROM technical_indicators
                    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    AND (sma_20 IS NULL OR ema_12 IS NULL OR rsi_14 IS NULL)
                """)
                incomplete_indicators = cursor.fetchone()[0]
                
                valid_symbols = symbols_with_indicators
                invalid_symbols = total_symbols - symbols_with_indicators
                coverage = (valid_symbols / max(total_symbols, 1)) * 100
                
                validation_errors = []
                if invalid_symbols > 0:
                    validation_errors.append(f"{invalid_symbols} symbols missing recent indicators")
                if incomplete_indicators > 0:
                    validation_errors.append(f"{incomplete_indicators} incomplete indicator records")
                
                return DataQualityReport(
                    total_records=total_symbols,
                    valid_records=valid_symbols,
                    invalid_records=invalid_symbols,
                    duplicate_records=0,  # Not applicable for technical indicators
                    validation_errors=validation_errors,
                    data_quality_score=coverage
                )
                
        except Exception as e:
            self.logger.error("technical_quality_report_error", error=str(e))
            return DataQualityReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                duplicate_records=0,
                validation_errors=[f"Error generating report: {str(e)}"],
                data_quality_score=0.0
            )

async def main():
    """Main function to run the enhanced technical calculator"""
    collector = EnhancedTechnicalCalculator()
    
    # Start the collection loop
    collection_task = asyncio.create_task(collector.run_collection_loop())
    
    # Start the web server for API endpoints
    server_task = asyncio.create_task(
        asyncio.to_thread(collector.run_server, host="0.0.0.0", port=8000)
    )
    
    # Wait for either task to complete (or shutdown signal)
    try:
        await asyncio.gather(collection_task, server_task, return_exceptions=True)
    except KeyboardInterrupt:
        collector.logger.info("shutdown_requested", signal="SIGINT")
        collector._shutdown_event.set()

if __name__ == "__main__":
    asyncio.run(main())