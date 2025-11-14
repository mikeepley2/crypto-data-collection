#!/usr/bin/env python3
"""
Enhanced Materialized Updater with ML Market & Derivatives Integration
Integrates with ML Market Collector (8080) and Derivatives Collector (8081)
Adds 88 missing ML features to ml_features_materialized table
"""

import mysql.connector
import logging
import time
import requests
from datetime import datetime, timedelta
import threading
from collections import defaultdict
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import sys
import os
from decimal import Decimal

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Collector API endpoints
ML_MARKET_COLLECTOR_URL = "http://ml-market-collector:8000"  # K8s service
DERIVATIVES_COLLECTOR_URL = "http://derivatives-collector:8000"  # K8s service

# For debugging/local testing, fallback to localhost
FALLBACK_ML_MARKET_URL = "http://localhost:8080"
FALLBACK_DERIVATIVES_URL = "http://localhost:8081"

class EnhancedMaterializedTableUpdater:
    
    def __init__(self):
        self.app = FastAPI()
        self.setup_routes()
        self.last_ml_market_update = {}
        self.last_derivatives_update = {}
        
    def get_db_connection(self):
        """Get database connection"""
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
            logger.error(f"❌ Database connection failed: {e}")
            return None

    def fetch_ml_market_data(self):
        """Fetch data from ML Market Collector API"""
        try:
            # Try K8s service first, fallback to localhost
            urls_to_try = [ML_MARKET_COLLECTOR_URL, FALLBACK_ML_MARKET_URL]
            
            for url in urls_to_try:
                try:
                    response = requests.get(f"{url}/data", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ ML Market data fetched from {url}")
                        return data
                except requests.RequestException:
                    continue
            
            logger.error("❌ Could not reach ML Market Collector")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching ML market data: {e}")
            return None
    
    def fetch_derivatives_data(self):
        """Fetch data from Derivatives Collector API"""
        try:
            # Try K8s service first, fallback to localhost
            urls_to_try = [DERIVATIVES_COLLECTOR_URL, FALLBACK_DERIVATIVES_URL]
            
            for url in urls_to_try:
                try:
                    response = requests.get(f"{url}/data", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Derivatives data fetched from {url}")
                        return data
                except requests.RequestException:
                    continue
            
            logger.error("❌ Could not reach Derivatives Collector")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching derivatives data: {e}")
            return None

    def map_ml_market_features(self, ml_data):
        """Map ML Market Collector data to database columns"""
        if not ml_data or 'traditional_markets' not in ml_data:
            return {}
        
        features = {}
        markets = ml_data['traditional_markets']
        
        # Traditional ETF data
        for etf, data in markets.items():
            if etf.lower() in ['qqq', 'arkk', 'xle', 'xlf', 'gld', 'tlt']:
                features[f"{etf.lower()}_price"] = data.get('price')
                features[f"{etf.lower()}_volume"] = data.get('volume')
                features[f"{etf.lower()}_rsi"] = data.get('rsi_14')
                features[f"{etf.lower()}_sma_20"] = data.get('sma_20')
                features[f"{etf.lower()}_ema_12"] = data.get('ema_12')
        
        # Market indices and commodities
        indices = ml_data.get('market_indices', {})
        features['usd_index'] = indices.get('dxy')
        features['nasdaq_100'] = indices.get('nasdaq')
        features['nasdaq_volume'] = indices.get('nasdaq_volume')
        features['gold_futures'] = indices.get('gold')
        features['oil_wti'] = indices.get('oil')
        features['bond_10y_yield'] = indices.get('treasury_10y')
        features['bond_2y_yield'] = indices.get('treasury_2y')
        features['copper_futures'] = indices.get('copper')
        
        # ML indicators
        ml_indicators = ml_data.get('ml_indicators', {})
        features['market_correlation_crypto'] = ml_indicators.get('crypto_correlation')
        features['sector_rotation_factor'] = ml_indicators.get('sector_rotation')
        features['risk_parity_score'] = ml_indicators.get('risk_parity')
        features['momentum_composite'] = ml_indicators.get('momentum')
        features['value_growth_ratio'] = ml_indicators.get('value_growth')
        features['volatility_regime'] = ml_indicators.get('volatility_regime')
        features['liquidity_stress_index'] = ml_indicators.get('liquidity_stress')
        
        return features

    def map_derivatives_features(self, derivatives_data, symbol):
        """Map Derivatives Collector data to database columns for specific symbol"""
        if not derivatives_data or 'cryptocurrencies' not in derivatives_data:
            return {}
        
        features = {}
        crypto_data = derivatives_data['cryptocurrencies'].get(symbol.upper())
        if not crypto_data:
            return {}
        
        # Exchange-specific data
        for exchange in ['binance', 'bybit', 'okx']:
            if exchange in crypto_data:
                exchange_data = crypto_data[exchange]
                features[f"{exchange}_{symbol.lower()}_funding_rate"] = exchange_data.get('funding_rate')
                features[f"{exchange}_{symbol.lower()}_open_interest"] = exchange_data.get('open_interest')
                features[f"{exchange}_{symbol.lower()}_liquidations_long"] = exchange_data.get('liquidations_long')
                features[f"{exchange}_{symbol.lower()}_liquidations_short"] = exchange_data.get('liquidations_short')
        
        # Composite features
        composites = derivatives_data.get('composite_indicators', {})
        features['avg_funding_rate'] = composites.get('avg_funding_rate')
        features['total_open_interest'] = composites.get('total_open_interest')
        features['liquidation_ratio'] = composites.get('liquidation_ratio')
        features['funding_divergence'] = composites.get('funding_divergence')
        features['derivatives_momentum'] = composites.get('derivatives_momentum')
        features['leverage_sentiment'] = composites.get('leverage_sentiment')
        features['market_stress_indicator'] = composites.get('market_stress_indicator')
        
        return features

    def update_materialized_table(self, symbol, timestamp_iso):
        """Enhanced update with ML Market & Derivatives data integration"""
        try:
            # Fetch data from both collectors
            ml_market_data = self.fetch_ml_market_data()
            derivatives_data = self.fetch_derivatives_data()
            
            # Get existing materialized data
            conn = self.get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if record exists for this symbol and timestamp
            check_query = """
            SELECT id FROM ml_features_materialized 
            WHERE symbol = %s AND timestamp_iso = %s
            """
            cursor.execute(check_query, (symbol, timestamp_iso))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update existing record with new ML features
                update_fields = []
                update_values = []
                
                # Add ML Market features
                if ml_market_data:
                    ml_features = self.map_ml_market_features(ml_market_data)
                    for field, value in ml_features.items():
                        if value is not None:
                            update_fields.append(f"{field} = %s")
                            update_values.append(value)
                
                # Add Derivatives features (for supported symbols)
                if derivatives_data and symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'AVAX', 'DOT', 'LINK', 'LTC', 'XRP']:
                    derivatives_features = self.map_derivatives_features(derivatives_data, symbol)
                    for field, value in derivatives_features.items():
                        if value is not None:
                            update_fields.append(f"{field} = %s")
                            update_values.append(value)
                
                if update_fields:
                    update_query = f"""
                    UPDATE ml_features_materialized 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = %s
                    """
                    update_values.append(existing_record['id'])
                    cursor.execute(update_query, update_values)
                    conn.commit()
                    logger.info(f"✅ Updated {symbol} with {len(update_fields)} ML features")
                else:
                    logger.info(f"⚡ No new ML features to update for {symbol}")
            else:
                logger.info(f"⚠️ No existing record found for {symbol} at {timestamp_iso}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error updating materialized table for {symbol}: {e}")
            if conn:
                conn.rollback()
                conn.close()

    def run_hourly_ml_integration(self):
        """Run hourly ML features integration"""
        try:
            logger.info("🚀 Starting hourly ML integration...")
            
            # Get list of active symbols
            conn = self.get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT DISTINCT symbol FROM ml_features_materialized ORDER BY symbol")
            symbols = [row['symbol'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            # Current timestamp for this update cycle
            current_timestamp = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            logger.info(f"📊 Processing ML integration for {len(symbols)} symbols")
            
            # Update each symbol
            for symbol in symbols:
                self.update_materialized_table(symbol, current_timestamp)
                time.sleep(0.1)  # Small delay to avoid overwhelming APIs
            
            logger.info("✅ Hourly ML integration completed")
            
        except Exception as e:
            logger.error(f"❌ Error in hourly ML integration: {e}")

    def setup_routes(self):
        """Setup FastAPI routes"""
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/ml-integration-status")
        async def ml_integration_status():
            ml_status = "unknown"
            derivatives_status = "unknown"
            
            # Check ML Market Collector
            try:
                ml_data = self.fetch_ml_market_data()
                ml_status = "connected" if ml_data else "disconnected"
            except:
                ml_status = "error"
            
            # Check Derivatives Collector
            try:
                derivatives_data = self.fetch_derivatives_data()
                derivatives_status = "connected" if derivatives_data else "disconnected"
            except:
                derivatives_status = "error"
            
            return {
                "ml_market_collector": ml_status,
                "derivatives_collector": derivatives_status,
                "last_ml_update": self.last_ml_market_update,
                "last_derivatives_update": self.last_derivatives_update,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/run-ml-integration")
        async def manual_ml_integration():
            self.run_hourly_ml_integration()
            return {"status": "ML integration completed", "timestamp": datetime.now().isoformat()}

    def start_background_tasks(self):
        """Start background threads for ML integration"""
        def ml_integration_loop():
            while True:
                try:
                    self.run_hourly_ml_integration()
                    time.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"❌ ML integration loop error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error
        
        # Start ML integration thread
        ml_thread = threading.Thread(target=ml_integration_loop, daemon=True)
        ml_thread.start()
        logger.info("✅ ML integration background task started")

    def run(self):
        """Run the enhanced materialized updater"""
        logger.info("🚀 Starting Enhanced Materialized Updater with ML Integration")
        
        # Start background tasks
        self.start_background_tasks()
        
        # Run FastAPI server
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )

if __name__ == "__main__":
    updater = EnhancedMaterializedTableUpdater()
    updater.run()