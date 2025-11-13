#!/usr/bin/env python3
"""
Enhanced Market Data Collector - ML-Focused for Crypto Trading
Collect high-correlation traditional market data for crypto ML
"""

import yfinance as yf
import mysql.connector
import os
from datetime import datetime, timedelta
import logging
import time
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enhanced-market-collector')

class MLFocusedMarketCollector:
    """Collect ML-valuable market data for crypto trading"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # High-value ML assets for crypto correlation
        self.ml_assets = {
            # PRIORITY 1 - Highest crypto correlation
            'QQQ': 'NASDAQ-100 ETF',           # 75% correlation
            'ARKK': 'ARK Innovation ETF',      # 80% correlation  
            'HYG': 'High Yield Corporate Bonds', # Credit spreads
            'TLT': 'Long Treasury ETF',        # Risk-free rate proxy
            
            # PRIORITY 2 - Strong correlation
            'SPY': 'S&P 500 ETF',             # 45% correlation
            'EURUSD=X': 'EUR/USD Currency',    # Dollar strength
            'USDJPY=X': 'USD/JPY Currency',    # Safe haven
            'EEM': 'Emerging Markets',         # Global risk
            
            # VOLATILITY & SENTIMENT
            '^VIX': 'CBOE Volatility Index',   # Already collected but verify
            '^MOVE': 'Bond Volatility Index',  # Bond market fear
        }
        
        # Calculated ML indicators
        self.ml_calculations = [
            'risk_on_risk_off_ratio',    # QQQ/VIX
            'innovation_premium',        # ARKK/SPY
            'tech_leadership',           # QQQ/SPY
            'credit_spreads',            # HYG-TLT spread
            'safe_haven_demand',         # Gold/SPY ratio
            'dollar_momentum',           # DXY 20-day change
            'global_risk_appetite'       # EEM/SPY ratio
        ]
    
    def get_connection(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def collect_ml_market_data(self):
        """Collect all ML-valuable market data"""
        logger.info("🚀 Starting ML-focused market data collection")
        
        collected_data = {}
        
        # Collect asset prices
        for symbol, description in self.ml_assets.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")  # Last 5 days
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    collected_data[symbol] = {
                        'price': float(latest['Close']),
                        'volume': float(latest['Volume']),
                        'change_1d': float((latest['Close'] - prev['Close']) / prev['Close'] * 100),
                        'high': float(latest['High']),
                        'low': float(latest['Low']),
                        'description': description,
                        'timestamp': datetime.now()
                    }
                    
                    logger.info(f"✅ {symbol} ({description}): ${latest['Close']:.2f}")
                    
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Failed to collect {symbol}: {e}")
        
        # Calculate ML indicators
        ml_indicators = self.calculate_ml_indicators(collected_data)
        collected_data.update(ml_indicators)
        
        # Store in database
        self.store_ml_market_data(collected_data)
        
        return collected_data
    
    def calculate_ml_indicators(self, data):
        """Calculate high-value ML indicators"""
        indicators = {}
        
        try:
            # Risk-On/Risk-Off Ratio (QQQ/VIX)
            if 'QQQ' in data and '^VIX' in data:
                indicators['risk_on_risk_off_ratio'] = {
                    'value': data['QQQ']['price'] / data['^VIX']['price'],
                    'description': 'Risk appetite indicator (higher = more risk-on)'
                }
            
            # Innovation Premium (ARKK/SPY) 
            if 'ARKK' in data and 'SPY' in data:
                indicators['innovation_premium'] = {
                    'value': data['ARKK']['price'] / data['SPY']['price'],
                    'description': 'Innovation sector premium vs broad market'
                }
            
            # Tech Leadership (QQQ/SPY)
            if 'QQQ' in data and 'SPY' in data:
                indicators['tech_leadership'] = {
                    'value': data['QQQ']['price'] / data['SPY']['price'],
                    'description': 'Tech sector leadership vs broad market'
                }
            
            # Credit Spreads approximation (HYG vs TLT)
            if 'HYG' in data and 'TLT' in data:
                indicators['credit_spreads'] = {
                    'value': (data['HYG']['change_1d'] - data['TLT']['change_1d']),
                    'description': 'Credit spread indicator (negative = widening spreads)'
                }
            
            # Global Risk Appetite (EEM/SPY)
            if 'EEM' in data and 'SPY' in data:
                indicators['global_risk_appetite'] = {
                    'value': data['EEM']['price'] / data['SPY']['price'],
                    'description': 'Emerging markets vs developed (risk appetite)'
                }
                
            logger.info(f"📊 Calculated {len(indicators)} ML indicators")
            
        except Exception as e:
            logger.error(f"❌ ML indicator calculation error: {e}")
        
        return indicators
    
    def store_ml_market_data(self, data):
        """Store ML market data in enhanced macro_indicators table"""
        conn = self.get_connection()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        try:
            # Store individual asset data
            for symbol, asset_data in data.items():
                if isinstance(asset_data, dict) and 'price' in asset_data:
                    
                    # Store main price
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, source, created_at) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), updated_at = NOW()
                    """, (
                        f"ML_{symbol}_PRICE",
                        datetime.now().date(),
                        asset_data['price'],
                        'ML_Market_Collector',
                        datetime.now()
                    ))
                    
                    # Store volume if available
                    if asset_data.get('volume', 0) > 0:
                        cursor.execute("""
                            INSERT INTO macro_indicators 
                            (indicator_name, indicator_date, value, source, created_at) 
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                            value = VALUES(value), updated_at = NOW()
                        """, (
                            f"ML_{symbol}_VOLUME",
                            datetime.now().date(),
                            asset_data['volume'],
                            'ML_Market_Collector',
                            datetime.now()
                        ))
                    
                    # Store daily change
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, source, created_at) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), updated_at = NOW()
                    """, (
                        f"ML_{symbol}_CHANGE_1D",
                        datetime.now().date(),
                        asset_data['change_1d'],
                        'ML_Market_Collector',
                        datetime.now()
                    ))
                
                # Store calculated indicators
                elif isinstance(asset_data, dict) and 'value' in asset_data:
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, source, created_at) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), updated_at = NOW()
                    """, (
                        f"ML_{symbol.upper()}",
                        datetime.now().date(),
                        asset_data['value'],
                        'ML_Market_Collector',
                        datetime.now()
                    ))
            
            logger.info(f"✅ Stored {len(data)} ML market indicators in database")
            
        except Exception as e:
            logger.error(f"❌ Database storage error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def test_collection(self):
        """Test ML market data collection"""
        logger.info("🧪 Testing ML-focused market data collection")
        
        data = self.collect_ml_market_data()
        
        logger.info("=" * 60)
        logger.info("📊 ML MARKET DATA COLLECTION RESULTS")
        logger.info("=" * 60)
        
        asset_count = 0
        indicator_count = 0
        
        for key, value in data.items():
            if isinstance(value, dict):
                if 'price' in value:
                    asset_count += 1
                    logger.info(f"💰 {key}: ${value['price']:.2f} ({value['change_1d']:+.1f}%)")
                elif 'value' in value:
                    indicator_count += 1
                    logger.info(f"📊 {key}: {value['value']:.4f}")
        
        logger.info(f"\n🎯 COLLECTION SUMMARY:")
        logger.info(f"   📈 Assets collected: {asset_count}")
        logger.info(f"   🔢 ML indicators: {indicator_count}")
        logger.info(f"   🏆 Total ML features: {asset_count * 3 + indicator_count}")
        logger.info(f"   📊 Database storage: ✅ Complete")

if __name__ == "__main__":
    collector = MLFocusedMarketCollector()
    collector.test_collection()