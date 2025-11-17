#!/usr/bin/env python3
"""
Enhanced Materialized Updater - Template Compliant Version
Migrated from legacy implementation to standardized collector template
"""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import mysql.connector
import json
from decimal import Decimal

from templates.collector_template.base_collector_template import (
    BaseCollector, CollectorConfig, DataQualityReport, AlertRequest
)

class MaterializedUpdaterConfig(CollectorConfig):
    """Extended configuration for materialized table updater"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(self, **kwargs)
        
        # Updater-specific configuration
        self.batch_processing_size = 20
        self.ml_market_api_url = "http://ml-market-collector:8000"
        self.derivatives_api_url = "http://derivatives-collector:8000"
        self.update_interval = 3600  # 1 hour
        
        # Supported symbols for derivatives data
        self.derivatives_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'AVAX', 'DOT', 'LINK', 'LTC', 'XRP']
        
        # ETF symbols for traditional market data
        self.etf_symbols = ['qqq', 'arkk', 'xle', 'xlf', 'gld', 'tlt']
        
        # Feature mapping configuration
        self.ml_feature_count = 88
        self.max_feature_age_hours = 24

    @classmethod
    def from_env(cls) -> 'MaterializedUpdaterConfig':
        """Load configuration from environment variables"""
        config = super().from_env()
        # Convert to MaterializedUpdaterConfig
        updater_config = cls(**config.__dict__)
        updater_config.service_name = "enhanced-materialized-updater"
        return updater_config

class EnhancedMaterializedUpdater(BaseCollector):
    """
    Enhanced Materialized Updater implementing the standardized collector template
    Updates materialized views with ML features from external data sources
    """
    
    def __init__(self):
        config = MaterializedUpdaterConfig.from_env()
        super().__init__(config)
        self.session = None

    async def collect_data(self) -> int:
        """
        Update materialized tables with ML features from external sources
        Returns number of records updated
        """
        self.logger.info("materialized_update_started")
        
        # Initialize HTTP session
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)) as session:
            self.session = session
            
            # Fetch external data sources
            ml_market_data = await self._fetch_ml_market_data()
            derivatives_data = await self._fetch_derivatives_data()
            
            # Get symbols to update
            symbols = await self._get_symbols_for_update()
            
            if not symbols:
                self.logger.warning("no_symbols_for_update")
                return 0
            
            updated_count = 0
            current_timestamp = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            
            # Process symbols in batches
            batch_size = self.config.batch_processing_size
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i + batch_size]
                
                for symbol in batch_symbols:
                    try:
                        # Rate limiting
                        if self.rate_limiter:
                            await self.rate_limiter.wait_for_token()
                        
                        success = await self._update_symbol_features(
                            symbol, current_timestamp, ml_market_data, derivatives_data
                        )
                        
                        if success:
                            updated_count += 1
                            self.metrics['records_processed_total'].labels(operation='materialized_update').inc()
                        
                    except Exception as e:
                        self.logger.error("symbol_update_error", symbol=symbol, error=str(e))
                        self.collection_errors += 1
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            # Send alert if too many errors
            if (self.config.enable_alerting and 
                self.collection_errors >= self.config.alert_error_threshold):
                await self._send_alert(AlertRequest(
                    alert_type="materialized_update_errors",
                    severity="warning", 
                    message=f"Multiple materialized update failures: {self.collection_errors}",
                    service=self.config.service_name,
                    additional_data={"errors": self.collection_errors, "total": len(symbols)}
                ))
        
        self.logger.info("materialized_update_completed", updated=updated_count)
        return updated_count

    async def _fetch_ml_market_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from ML Market Collector API"""
        
        try:
            # Circuit breaker for external API calls
            return await self.circuit_breaker.call_async(self._fetch_ml_market_api)
            
        except Exception as e:
            self.logger.error("ml_market_data_fetch_error", error=str(e))
            return None

    async def _fetch_ml_market_api(self) -> Dict[str, Any]:
        """Internal method to fetch ML market data"""
        
        url = f"{self.config.ml_market_api_url}/data"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.debug("ml_market_data_fetched_successfully")
                self.metrics['api_requests_total'].labels(endpoint=url, status='success').inc()
                return data
            else:
                self.logger.warning("ml_market_api_error", status=response.status, url=url)
                self.metrics['api_requests_total'].labels(endpoint=url, status='error').inc()
                return {}

    async def _fetch_derivatives_data(self) -> Optional[Dict[str, Any]]:
        """Fetch data from Derivatives Collector API"""
        
        try:
            # Circuit breaker for external API calls
            return await self.circuit_breaker.call_async(self._fetch_derivatives_api)
            
        except Exception as e:
            self.logger.error("derivatives_data_fetch_error", error=str(e))
            return None

    async def _fetch_derivatives_api(self) -> Dict[str, Any]:
        """Internal method to fetch derivatives data"""
        
        url = f"{self.config.derivatives_api_url}/data"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                self.logger.debug("derivatives_data_fetched_successfully")
                self.metrics['api_requests_total'].labels(endpoint=url, status='success').inc()
                return data
            else:
                self.logger.warning("derivatives_api_error", status=response.status, url=url)
                self.metrics['api_requests_total'].labels(endpoint=url, status='error').inc()
                return {}

    async def _get_symbols_for_update(self) -> List[str]:
        """Get list of symbols that need materialized updates"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol 
                    FROM ml_features_materialized 
                    ORDER BY symbol
                """)
                
                symbols = [row[0] for row in cursor.fetchall()]
                self.logger.info("symbols_for_update_loaded", count=len(symbols))
                return symbols
                
        except Exception as e:
            self.logger.error("failed_to_load_update_symbols", error=str(e))
            # Fallback to common symbols
            return ['BTC', 'ETH', 'ADA', 'SOL', 'DOT']

    async def _update_symbol_features(
        self, 
        symbol: str, 
        timestamp: datetime, 
        ml_market_data: Optional[Dict], 
        derivatives_data: Optional[Dict]
    ) -> bool:
        """Update materialized features for a single symbol"""
        
        try:
            # Check if record exists
            record_exists = await self._check_record_exists(symbol, timestamp)
            
            if not record_exists:
                self.logger.debug("no_existing_record", symbol=symbol, timestamp=timestamp)
                return False
            
            # Build feature updates
            feature_updates = {}
            
            # Add ML Market features
            if ml_market_data:
                ml_features = self._map_ml_market_features(ml_market_data)
                feature_updates.update(ml_features)
            
            # Add Derivatives features (for supported symbols)
            if derivatives_data and symbol.upper() in self.config.derivatives_symbols:
                derivatives_features = self._map_derivatives_features(derivatives_data, symbol)
                feature_updates.update(derivatives_features)
            
            if not feature_updates:
                self.logger.debug("no_feature_updates", symbol=symbol)
                return True
            
            # Data validation if enabled
            if self.config.enable_data_validation:
                validation_result = await self._validate_data({
                    "symbol": symbol,
                    "timestamp": timestamp,
                    "feature_count": len(feature_updates)
                })
                if not validation_result["is_valid"]:
                    self.logger.warning("feature_validation_failed", 
                                      symbol=symbol,
                                      errors=validation_result["errors"])
                    return False
            
            # Update database
            success = await self._update_features_in_db(symbol, timestamp, feature_updates)
            
            if success:
                self.logger.debug("symbol_features_updated", 
                                symbol=symbol, features=len(feature_updates))
            
            return success
            
        except Exception as e:
            self.logger.error("symbol_feature_update_error", symbol=symbol, error=str(e))
            raise

    async def _check_record_exists(self, symbol: str, timestamp: datetime) -> bool:
        """Check if a record exists for the symbol and timestamp"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM ml_features_materialized 
                    WHERE symbol = %s AND timestamp_iso = %s
                """, (symbol, timestamp))
                
                result = cursor.fetchone()
                return result is not None
                
        except Exception as e:
            self.logger.error("record_existence_check_error", symbol=symbol, error=str(e))
            return False

    def _map_ml_market_features(self, ml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map ML Market Collector data to database columns"""
        
        if not ml_data or 'traditional_markets' not in ml_data:
            return {}
        
        features = {}
        
        try:
            # Traditional ETF data
            traditional_markets = ml_data.get('traditional_markets', {})
            for etf in self.config.etf_symbols:
                etf_data = traditional_markets.get(etf.upper(), {})
                if etf_data:
                    features[f"{etf}_price"] = etf_data.get('price')
                    features[f"{etf}_volume"] = etf_data.get('volume')
                    features[f"{etf}_rsi"] = etf_data.get('rsi_14')
                    features[f"{etf}_sma_20"] = etf_data.get('sma_20')
                    features[f"{etf}_ema_12"] = etf_data.get('ema_12')
            
            # Market indices and commodities
            market_indices = ml_data.get('market_indices', {})
            features.update({
                'usd_index': market_indices.get('dxy'),
                'nasdaq_100': market_indices.get('nasdaq'),
                'nasdaq_volume': market_indices.get('nasdaq_volume'),
                'gold_futures': market_indices.get('gold'),
                'oil_wti': market_indices.get('oil'),
                'bond_10y_yield': market_indices.get('treasury_10y'),
                'bond_2y_yield': market_indices.get('treasury_2y'),
                'copper_futures': market_indices.get('copper')
            })
            
            # ML indicators
            ml_indicators = ml_data.get('ml_indicators', {})
            features.update({
                'market_correlation_crypto': ml_indicators.get('crypto_correlation'),
                'sector_rotation_factor': ml_indicators.get('sector_rotation'),
                'risk_parity_score': ml_indicators.get('risk_parity'),
                'momentum_composite': ml_indicators.get('momentum'),
                'value_growth_ratio': ml_indicators.get('value_growth'),
                'volatility_regime': ml_indicators.get('volatility_regime'),
                'liquidity_stress_index': ml_indicators.get('liquidity_stress')
            })
            
            # Filter out None values
            features = {k: v for k, v in features.items() if v is not None}
            
            return features
            
        except Exception as e:
            self.logger.error("ml_market_feature_mapping_error", error=str(e))
            return {}

    def _map_derivatives_features(self, derivatives_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Map Derivatives Collector data to database columns for specific symbol"""
        
        if not derivatives_data or 'cryptocurrencies' not in derivatives_data:
            return {}
        
        features = {}
        
        try:
            crypto_data = derivatives_data['cryptocurrencies'].get(symbol.upper(), {})
            if not crypto_data:
                return {}
            
            # Exchange-specific data
            for exchange in ['binance', 'bybit', 'okx']:
                exchange_data = crypto_data.get(exchange, {})
                if exchange_data:
                    features.update({
                        f"{exchange}_{symbol.lower()}_funding_rate": exchange_data.get('funding_rate'),
                        f"{exchange}_{symbol.lower()}_open_interest": exchange_data.get('open_interest'),
                        f"{exchange}_{symbol.lower()}_liquidations_long": exchange_data.get('liquidations_long'),
                        f"{exchange}_{symbol.lower()}_liquidations_short": exchange_data.get('liquidations_short')
                    })
            
            # Composite features
            composite_indicators = derivatives_data.get('composite_indicators', {})
            features.update({
                'avg_funding_rate': composite_indicators.get('avg_funding_rate'),
                'total_open_interest': composite_indicators.get('total_open_interest'),
                'liquidation_ratio': composite_indicators.get('liquidation_ratio'),
                'funding_divergence': composite_indicators.get('funding_divergence'),
                'derivatives_momentum': composite_indicators.get('derivatives_momentum'),
                'leverage_sentiment': composite_indicators.get('leverage_sentiment'),
                'market_stress_indicator': composite_indicators.get('market_stress_indicator')
            })
            
            # Filter out None values
            features = {k: v for k, v in features.items() if v is not None}
            
            return features
            
        except Exception as e:
            self.logger.error("derivatives_feature_mapping_error", symbol=symbol, error=str(e))
            return {}

    async def _update_features_in_db(self, symbol: str, timestamp: datetime, features: Dict[str, Any]) -> bool:
        """Update features in the database"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                update_fields = []
                update_values = []
                
                for field, value in features.items():
                    if value is not None:
                        # Handle different data types
                        if isinstance(value, (int, float, Decimal)):
                            update_fields.append(f"{field} = %s")
                            update_values.append(float(value))
                        else:
                            update_fields.append(f"{field} = %s") 
                            update_values.append(value)
                
                if not update_fields:
                    return True
                
                # Execute update
                update_query = f"""
                    UPDATE ml_features_materialized 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE symbol = %s AND timestamp_iso = %s
                """
                
                update_values.extend([symbol, timestamp])
                cursor.execute(update_query, update_values)
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.metrics['database_operations_total'].labels(operation='feature_update', status='success').inc()
                    return True
                else:
                    self.logger.warning("no_rows_updated", symbol=symbol)
                    return False
                
        except Exception as e:
            self.logger.error("feature_db_update_error", symbol=symbol, error=str(e))
            self.metrics['database_operations_total'].labels(operation='feature_update', status='error').inc()
            raise

    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """
        Backfill missing materialized updates for historical periods
        """
        
        self.logger.info("materialized_backfill_started", periods=len(missing_periods), force=force)
        
        total_updated = 0
        
        try:
            # For materialized updates, backfill involves re-running updates for historical periods
            for period in missing_periods:
                try:
                    symbols = await self._get_symbols_for_update()
                    
                    # For each period, attempt to update with current external data
                    # (Note: Historical external data may not be available)
                    async with aiohttp.ClientSession() as session:
                        self.session = session
                        ml_market_data = await self._fetch_ml_market_data()
                        derivatives_data = await self._fetch_derivatives_data()
                        
                        for symbol in symbols:
                            if self.rate_limiter:
                                await self.rate_limiter.wait_for_token()
                            
                            # Use period timestamp if available
                            if "start_date" in period:
                                timestamp = period["start_date"]
                            elif "date" in period:
                                timestamp = period["date"]
                            else:
                                timestamp = datetime.now(timezone.utc)
                            
                            success = await self._update_symbol_features(
                                symbol, timestamp, ml_market_data, derivatives_data
                            )
                            
                            if success:
                                total_updated += 1
                            
                            await asyncio.sleep(0.1)
                
                except Exception as e:
                    self.logger.error("backfill_period_error", period=period, error=str(e))
        
        except Exception as e:
            self.logger.error("materialized_backfill_error", error=str(e))
            raise
        
        self.logger.info("materialized_backfill_completed", updated=total_updated)
        return total_updated

    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """Get status of materialized tables"""
        
        try:
            # Get overall statistics
            cursor.execute("""
                SELECT COUNT(*) as total_records,
                       COUNT(DISTINCT symbol) as symbols_count,
                       MAX(updated_at) as last_update,
                       MIN(timestamp_iso) as earliest_data,
                       MAX(timestamp_iso) as latest_data
                FROM ml_features_materialized
            """)
            
            result = cursor.fetchone()
            
            # Get recent update statistics
            cursor.execute("""
                SELECT symbol, 
                       MAX(updated_at) as last_update,
                       COUNT(*) as record_count
                FROM ml_features_materialized 
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                GROUP BY symbol
                ORDER BY last_update DESC
                LIMIT 10
            """)
            
            recent_updates = {row[0]: {"last_update": row[1], "records": row[2]} 
                            for row in cursor.fetchall()}
            
            # Check ML feature completeness
            cursor.execute("""
                SELECT COUNT(*) as records_with_ml_features
                FROM ml_features_materialized
                WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                AND (qqq_price IS NOT NULL OR avg_funding_rate IS NOT NULL)
            """)
            
            ml_feature_coverage = cursor.fetchone()[0]
            
            return {
                "ml_features_materialized": {
                    "total_records": result[0] if result else 0,
                    "symbols_count": result[1] if result else 0,
                    "last_update": result[2] if result and result[2] else None,
                    "earliest_data": result[3] if result and result[3] else None,
                    "latest_data": result[4] if result and result[4] else None,
                    "recent_updates": recent_updates,
                    "ml_feature_coverage": ml_feature_coverage
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
        Analyze missing materialized update data
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Find records with missing ML features
                if symbols:
                    symbol_condition = "AND symbol IN ({})".format(",".join(["'"+s+"'" for s in symbols]))
                else:
                    symbol_condition = ""
                
                cursor.execute(f"""
                    SELECT symbol, DATE(timestamp_iso) as update_date,
                           COUNT(*) as total_records,
                           COUNT(CASE WHEN qqq_price IS NULL THEN 1 END) as missing_ml_market,
                           COUNT(CASE WHEN avg_funding_rate IS NULL THEN 1 END) as missing_derivatives
                    FROM ml_features_materialized
                    WHERE timestamp_iso BETWEEN %s AND %s
                    {symbol_condition}
                    GROUP BY symbol, DATE(timestamp_iso)
                    HAVING missing_ml_market > 0 OR missing_derivatives > 0
                    ORDER BY symbol, update_date
                """, (start_date, end_date))
                
                results = cursor.fetchall()
                
                missing_periods = []
                for symbol, update_date, total_records, missing_ml_market, missing_derivatives in results:
                    missing_periods.append({
                        "symbol": symbol,
                        "date": update_date,
                        "total_records": total_records,
                        "missing_ml_market": missing_ml_market,
                        "missing_derivatives": missing_derivatives,
                        "reason": "incomplete_ml_features"
                    })
                
                return missing_periods
                
        except Exception as e:
            self.logger.error("missing_materialized_analysis_error", error=str(e))
            return []

    async def _estimate_backfill_records(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> int:
        """
        Estimate number of materialized records that would be backfilled
        """
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                if symbols:
                    symbol_condition = "AND symbol IN ({})".format(",".join(["'"+s+"'" for s in symbols]))
                else:
                    symbol_condition = ""
                
                cursor.execute(f"""
                    SELECT COUNT(*) FROM ml_features_materialized
                    WHERE timestamp_iso BETWEEN %s AND %s
                    {symbol_condition}
                    AND (qqq_price IS NULL OR avg_funding_rate IS NULL)
                """, (start_date, end_date))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error("materialized_backfill_estimation_error", error=str(e))
            return 0

    async def _get_required_fields(self) -> List[str]:
        """Get required fields for data validation"""
        return ["symbol", "timestamp", "feature_count"]

    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Generate comprehensive data quality report for materialized tables"""
        
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Get total records
                cursor.execute("""
                    SELECT COUNT(*) FROM ml_features_materialized
                    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                """)
                total_records = cursor.fetchone()[0]
                
                # Get records with ML features
                cursor.execute("""
                    SELECT COUNT(*) FROM ml_features_materialized
                    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    AND (qqq_price IS NOT NULL OR arkk_price IS NOT NULL OR avg_funding_rate IS NOT NULL)
                """)
                records_with_features = cursor.fetchone()[0]
                
                # Get records with null/missing features
                cursor.execute("""
                    SELECT COUNT(*) FROM ml_features_materialized
                    WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
                    AND qqq_price IS NULL AND arkk_price IS NULL AND avg_funding_rate IS NULL
                """)
                incomplete_records = cursor.fetchone()[0]
                
                valid_records = records_with_features
                invalid_records = total_records - valid_records
                completeness = (valid_records / max(total_records, 1)) * 100
                
                validation_errors = []
                if invalid_records > 0:
                    validation_errors.append(f"{invalid_records} records missing ML features")
                if incomplete_records > 0:
                    validation_errors.append(f"{incomplete_records} records completely empty")
                
                return DataQualityReport(
                    total_records=total_records,
                    valid_records=valid_records,
                    invalid_records=invalid_records,
                    duplicate_records=0,  # Not applicable for materialized updates
                    validation_errors=validation_errors,
                    data_quality_score=completeness
                )
                
        except Exception as e:
            self.logger.error("materialized_quality_report_error", error=str(e))
            return DataQualityReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                duplicate_records=0,
                validation_errors=[f"Error generating report: {str(e)}"],
                data_quality_score=0.0
            )

async def main():
    """Main function to run the enhanced materialized updater"""
    collector = EnhancedMaterializedUpdater()
    
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