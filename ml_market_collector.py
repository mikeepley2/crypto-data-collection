#!/usr/bin/env python3
"""
ML-Focused Market Data Collector
Collects high-correlation traditional market data for crypto ML trading
Uses centralized configuration and connection pooling
"""

import os
import sys
import logging
import time
import json
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import schedule
from contextlib import contextmanager

# Import centralized scheduling configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.scheduling_config import get_collector_schedule, create_schedule_for_collector
except ImportError as e:
    logging.warning(f"Could not import centralized scheduling config: {e}. Using defaults.")
    get_collector_schedule = None
    create_schedule_for_collector = None

# Import shared database pool
try:
    sys.path.append("/app/shared")
    from shared.database_pool import get_connection_context, execute_query, get_pool_stats
    SHARED_POOL_AVAILABLE = True
except ImportError:
    SHARED_POOL_AVAILABLE = False
    # Import centralized database configuration as fallback
    try:
        from shared.database_config import get_db_connection
        def get_connection_fallback():
            """Use centralized database configuration"""
            return get_db_connection()
    except ImportError:
        # Final fallback
        import mysql.connector
        def get_connection_fallback():
            return mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "host.docker.internal"),
                port=int(os.getenv("MYSQL_PORT", 3306)),
                user=os.getenv("MYSQL_USER", "news_collector"),
                password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
                database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
                charset="utf8mb4",
                autocommit=True
            )

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ml-market-collector")

class MLMarketDataCollector:
    """ML-focused market data collector using centralized configuration"""
    
    def __init__(self):
        """Initialize collector with centralized configuration"""
        
        # High-correlation ML assets for crypto trading - Complete Coverage
        self.ml_assets = {
            # PRIORITY 1 - Highest crypto correlation (>70%)
            'QQQ': {
                'name': 'NASDAQ-100 ETF',
                'correlation': 0.75,
                'ml_value': 'HIGH',
                'category': 'TECH_EQUITY'
            },
            'ARKK': {
                'name': 'ARK Innovation ETF', 
                'correlation': 0.80,
                'ml_value': 'HIGH',
                'category': 'INNOVATION'
            },
            
            # Sector ETFs (Missing from Column Mapping - Columns 145-169)
            'XLE': {
                'name': 'Energy Select Sector SPDR',
                'correlation': 0.25,
                'ml_value': 'HIGH',
                'category': 'SECTOR'
            },
            'XLF': {
                'name': 'Financial Select Sector SPDR',
                'correlation': 0.60,
                'ml_value': 'HIGH',
                'category': 'SECTOR'
            },
            'XLY': {
                'name': 'Consumer Discretionary SPDR',
                'correlation': 0.65,
                'ml_value': 'HIGH',
                'category': 'SECTOR'
            },
            'XLP': {
                'name': 'Consumer Staples SPDR',
                'correlation': 0.30,
                'ml_value': 'HIGH',
                'category': 'SECTOR'
            },
            'XLK': {
                'name': 'Technology Select Sector SPDR',
                'correlation': 0.75,
                'ml_value': 'HIGH',
                'category': 'SECTOR'
            },
            
            # PRIORITY 2 - Strong correlation (40-70%)
            'SPY': {
                'name': 'S&P 500 ETF',
                'correlation': 0.45,
                'ml_value': 'MEDIUM',
                'category': 'BROAD_EQUITY'
            },
            'HYG': {
                'name': 'High Yield Corporate Bonds',
                'correlation': 0.60,
                'ml_value': 'HIGH',
                'category': 'CREDIT'
            },
            'TLT': {
                'name': 'Long Treasury ETF',
                'correlation': -0.40,
                'ml_value': 'HIGH', 
                'category': 'TREASURY'
            },
            'IEF': {
                'name': '7-10 Year Treasury ETF',
                'correlation': -0.35,
                'ml_value': 'HIGH',
                'category': 'TREASURY'
            },
            'SHY': {
                'name': '1-3 Year Treasury ETF',
                'correlation': -0.25,
                'ml_value': 'MEDIUM',
                'category': 'TREASURY'
            },
            
            # CURRENCIES - Dollar strength indicators
            'EURUSD=X': {
                'name': 'EUR/USD Currency Pair',
                'correlation': -0.35,
                'ml_value': 'HIGH',
                'category': 'CURRENCY'
            },
            'USDJPY=X': {
                'name': 'USD/JPY Currency Pair',
                'correlation': 0.25,
                'ml_value': 'HIGH',
                'category': 'CURRENCY'
            },
            'GBPUSD=X': {
                'name': 'GBP/USD Currency Pair',
                'correlation': -0.30,
                'ml_value': 'HIGH',
                'category': 'CURRENCY'
            },
            'CNYUSD=X': {
                'name': 'USD/CNY Currency Pair',
                'correlation': 0.20,
                'ml_value': 'MEDIUM',
                'category': 'CURRENCY'
            },
            'UUP': {
                'name': 'US Dollar Index ETF',
                'correlation': -0.50,
                'ml_value': 'HIGH',
                'category': 'CURRENCY'
            },
            
            # COMMODITIES - Enhanced coverage
            'GC=F': {
                'name': 'Gold Futures',
                'correlation': 0.30,
                'ml_value': 'HIGH',
                'category': 'COMMODITY'
            },
            'SI=F': {
                'name': 'Silver Futures',
                'correlation': 0.40,
                'ml_value': 'HIGH',
                'category': 'COMMODITY'
            },
            'CL=F': {
                'name': 'WTI Crude Oil Futures',
                'correlation': 0.20,
                'ml_value': 'HIGH',
                'category': 'COMMODITY'
            },
            'HG=F': {
                'name': 'Copper Futures',
                'correlation': 0.35,
                'ml_value': 'HIGH',
                'category': 'COMMODITY'
            },
            'NG=F': {
                'name': 'Natural Gas Futures',
                'correlation': 0.15,
                'ml_value': 'MEDIUM',
                'category': 'COMMODITY'
            },
            
            # GLOBAL RISK INDICATORS
            'EEM': {
                'name': 'Emerging Markets ETF',
                'correlation': 0.50,
                'ml_value': 'HIGH',
                'category': 'GLOBAL_EQUITY'
            },
            'EFA': {
                'name': 'International Developed Markets',
                'correlation': 0.40,
                'ml_value': 'MEDIUM',
                'category': 'GLOBAL_EQUITY'
            },
            'EWJ': {
                'name': 'Japan ETF (iShares MSCI)',
                'correlation': 0.25,
                'ml_value': 'MEDIUM',
                'category': 'GLOBAL_EQUITY'
            },
            'FXI': {
                'name': 'China Large Cap ETF',
                'correlation': 0.30,
                'ml_value': 'MEDIUM',
                'category': 'GLOBAL_EQUITY'
            },
            
            # VOLATILITY INDICATORS
            '^VIX': {
                'name': 'CBOE Volatility Index',
                'correlation': -0.65,
                'ml_value': 'HIGH',
                'category': 'VOLATILITY'
            },
            '^MOVE': {
                'name': 'Bond Volatility Index',
                'correlation': -0.35,
                'ml_value': 'MEDIUM',
                'category': 'VOLATILITY'
            },
            
            # CRYPTO-CORRELATED ETFs
            'BLOK': {
                'name': 'Amplify Blockchain ETF',
                'correlation': 0.85,
                'ml_value': 'HIGH',
                'category': 'CRYPTO_ETF'
            },
            'BITW': {
                'name': 'Bitwise Crypto Fund',
                'correlation': 0.90,
                'ml_value': 'HIGH',
                'category': 'CRYPTO_ETF'
            }
        }
        
        # Enhanced ML assets for traditional market coverage
        self.enhanced_ml_assets = {
            # Enhanced Commodities  
            'GC=F': {'name': 'Gold Futures', 'correlation': 0.3, 'ml_value': 'HIGH', 'category': 'COMMODITY'},
            'SI=F': {'name': 'Silver Futures', 'correlation': 0.4, 'ml_value': 'HIGH', 'category': 'COMMODITY'},
            'CL=F': {'name': 'WTI Crude Oil', 'correlation': 0.2, 'ml_value': 'HIGH', 'category': 'COMMODITY'},
            'HG=F': {'name': 'Copper Futures', 'correlation': 0.35, 'ml_value': 'HIGH', 'category': 'COMMODITY'},
            'NG=F': {'name': 'Natural Gas', 'correlation': 0.15, 'ml_value': 'MEDIUM', 'category': 'COMMODITY'},
            
            # Enhanced Sector ETFs (Missing from Column Mapping)
            'XLE': {'name': 'Energy Select Sector', 'correlation': 0.25, 'ml_value': 'HIGH', 'category': 'SECTOR'},
            'XLF': {'name': 'Financial Select Sector', 'correlation': 0.60, 'ml_value': 'HIGH', 'category': 'SECTOR'},
            'XLY': {'name': 'Consumer Discretionary', 'correlation': 0.65, 'ml_value': 'HIGH', 'category': 'SECTOR'},
            'XLP': {'name': 'Consumer Staples', 'correlation': 0.30, 'ml_value': 'HIGH', 'category': 'SECTOR'},
            'XLK': {'name': 'Technology Select Sector', 'correlation': 0.75, 'ml_value': 'HIGH', 'category': 'SECTOR'},
            
            # Enhanced Bond ETFs
            'TLT': {'name': '20+ Year Treasury Bond', 'correlation': -0.40, 'ml_value': 'HIGH', 'category': 'BOND'},
            'IEF': {'name': '7-10 Year Treasury', 'correlation': -0.35, 'ml_value': 'HIGH', 'category': 'BOND'},
            'SHY': {'name': '1-3 Year Treasury', 'correlation': -0.25, 'ml_value': 'MEDIUM', 'category': 'BOND'},
            
            # Global Currency ETFs
            'UUP': {'name': 'US Dollar Index ETF', 'correlation': -0.50, 'ml_value': 'HIGH', 'category': 'CURRENCY'},
            'FXE': {'name': 'Euro Currency ETF', 'correlation': 0.40, 'ml_value': 'MEDIUM', 'category': 'CURRENCY'},
            'FXY': {'name': 'Japanese Yen ETF', 'correlation': -0.20, 'ml_value': 'MEDIUM', 'category': 'CURRENCY'},
            
            # Enhanced Crypto-correlated ETFs
            'BLOK': {'name': 'Amplify Blockchain ETF', 'correlation': 0.85, 'ml_value': 'HIGH', 'category': 'CRYPTO_ETF'},
            'BITW': {'name': 'Bitwise Crypto Fund', 'correlation': 0.90, 'ml_value': 'HIGH', 'category': 'CRYPTO_ETF'},
            
            # Global Market ETFs  
            'EWJ': {'name': 'Japan ETF', 'correlation': 0.25, 'ml_value': 'MEDIUM', 'category': 'GLOBAL'},
            'FXI': {'name': 'China Large Cap ETF', 'correlation': 0.30, 'ml_value': 'MEDIUM', 'category': 'GLOBAL'},
            'EWZ': {'name': 'Brazil ETF', 'correlation': 0.40, 'ml_value': 'MEDIUM', 'category': 'GLOBAL'},
        }
        
        # ML calculation definitions
        self.ml_calculations = [
            {
                'name': 'risk_on_risk_off_ratio',
                'description': 'Market regime indicator (QQQ/VIX)',
                'formula': 'QQQ_price / VIX_price',
                'ml_value': 'CRITICAL'
            },
            {
                'name': 'innovation_premium', 
                'description': 'Innovation sector premium (ARKK/SPY)',
                'formula': 'ARKK_price / SPY_price',
                'ml_value': 'HIGH'
            },
            {
                'name': 'tech_leadership',
                'description': 'Tech sector leadership (QQQ/SPY)', 
                'formula': 'QQQ_price / SPY_price',
                'ml_value': 'HIGH'
            },
            {
                'name': 'credit_spreads_proxy',
                'description': 'Credit conditions (HYG vs TLT performance)',
                'formula': 'HYG_change_1d - TLT_change_1d',
                'ml_value': 'HIGH'
            },
            {
                'name': 'global_risk_appetite',
                'description': 'Emerging vs developed markets (EEM/SPY)',
                'formula': 'EEM_price / SPY_price', 
                'ml_value': 'HIGH'
            },
            {
                'name': 'dollar_strength_composite',
                'description': 'Dollar strength from currency pairs',
                'formula': '(1/EURUSD + USDJPY/100) / 2',
                'ml_value': 'MEDIUM'
            },
            {
                'name': 'volatility_regime',
                'description': 'Cross-asset volatility environment',
                'formula': '(VIX + MOVE) / 2',
                'ml_value': 'HIGH'
            }
        ]
        
        # Initialize FastAPI app
        self.app = FastAPI(title="ML Market Data Collector", version="1.0.0")
        self.setup_routes()
        
        # Collection statistics
        self.collection_stats = {
            'last_collection': None,
            'total_collections': 0,
            'assets_collected': 0,
            'ml_indicators_calculated': 0,
            'database_writes': 0
        }
        
        logger.info("🚀 Enhanced ML Market Data Collector initialized")
        logger.info(f"📊 Tracking {len(self.ml_assets)} high-correlation assets") 
        logger.info(f"🌍 Enhanced with {len(self.enhanced_ml_assets)} additional macro/sector assets")
        logger.info(f"🧠 Calculating ML indicators for enhanced market analysis")

    async def collect_enhanced_market_data(self) -> Dict:
        """Collect enhanced market data including new ETFs and sectors"""
        try:
            enhanced_data = {}
            
            # Collect enhanced assets using yfinance
            enhanced_symbols = [symbol for symbol in self.enhanced_ml_assets.keys() 
                              if self.enhanced_ml_assets[symbol].get('source') != 'FRED']
            
            if enhanced_symbols:
                enhanced_tickers = yf.download(enhanced_symbols, period='1d', interval='1d', progress=False)
                
                for symbol in enhanced_symbols:
                    try:
                        if symbol in enhanced_tickers['Close'].columns:
                            price = enhanced_tickers['Close'][symbol].iloc[-1]
                            enhanced_data[f'enhanced_{symbol.replace("=", "").replace("^", "").replace("-", "_").lower()}'] = float(price)
                        elif len(enhanced_symbols) == 1:  # Single symbol case
                            enhanced_data[f'enhanced_{symbol.replace("=", "").replace("^", "").replace("-", "_").lower()}'] = float(enhanced_tickers['Close'].iloc[-1])
                    except Exception as e:
                        logger.warning(f"Enhanced asset {symbol} error: {e}")
                        
            logger.info(f"✅ Collected {len(enhanced_data)} enhanced market assets")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Enhanced market data collection failed: {e}")
            return {}

    def calculate_enhanced_ml_indicators(self, all_data: Dict) -> Dict:
        """Calculate enhanced ML indicators from all collected data"""
        try:
            enhanced_indicators = {}
            
            # Yield curve indicators
            dgs10 = all_data.get('fred_dgs10')
            dgs2 = all_data.get('fred_dgs2') 
            dgs1 = all_data.get('fred_dgs1')
            
            if dgs10 and dgs2:
                enhanced_indicators['yield_curve_2_10'] = dgs10 - dgs2
                
            if dgs10 and dgs1:
                enhanced_indicators['yield_curve_1_10'] = dgs10 - dgs1
                
            # Real interest rate proxy
            fedfunds = all_data.get('fred_fedfunds')
            cpi = all_data.get('fred_cpiaucsl')
            if fedfunds is not None and cpi is not None:
                # Simplified real rate calculation
                enhanced_indicators['real_interest_rate_proxy'] = fedfunds - (cpi * 0.1)  # Rough inflation rate
                
            # Crypto correlation with blockchain ETFs
            blok_price = all_data.get('enhanced_blok')
            spy_price = all_data.get('SPY')
            if blok_price and spy_price:
                enhanced_indicators['blockchain_etf_ratio'] = blok_price / spy_price
                
            # Technology sector momentum
            xlk_price = all_data.get('enhanced_xlk')
            if xlk_price and spy_price:
                enhanced_indicators['tech_sector_momentum'] = xlk_price / spy_price
                
            # Commodity correlation
            gold_price = all_data.get('enhanced_gc_f', all_data.get('enhanced_gld'))
            if gold_price:
                enhanced_indicators['gold_to_spy_ratio'] = gold_price / spy_price if spy_price else 0
                
            # Risk-on/Risk-off sentiment
            vix = all_data.get('VIX')
            arkk = all_data.get('ARKK')
            if vix and arkk and spy_price:
                enhanced_indicators['risk_sentiment_composite'] = (arkk / spy_price) / (vix / 20)  # Normalize VIX
                
            logger.info(f"✅ Calculated {len(enhanced_indicators)} enhanced ML indicators")
            return enhanced_indicators
            
        except Exception as e:
            logger.warning(f"Enhanced ML indicator calculation error: {e}")
            return {}
    
    @contextmanager
    def get_connection(self):
        """Get database connection using centralized configuration"""
        if SHARED_POOL_AVAILABLE:
            with get_connection_context() as conn:
                yield conn
        else:
            conn = None
            try:
                conn = get_connection_fallback()
                yield conn
            finally:
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
    
    def collect_asset_data(self, symbol: str, asset_info: Dict) -> Optional[Dict]:
        """Collect data for a single asset"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if hist.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Calculate additional metrics
            change_1d = float((latest['Close'] - prev['Close']) / prev['Close'] * 100)
            volatility_5d = float(hist['Close'].pct_change().std() * 100)
            volume_avg_5d = float(hist['Volume'].mean()) if 'Volume' in hist.columns else 0
            
            asset_data = {
                'symbol': symbol,
                'name': asset_info['name'],
                'category': asset_info['category'],
                'correlation': asset_info['correlation'],
                'ml_value': asset_info['ml_value'],
                
                # Price data
                'price': float(latest['Close']),
                'volume': float(latest['Volume']) if 'Volume' in latest else 0,
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'open': float(latest['Open']),
                
                # Calculated metrics
                'change_1d_pct': change_1d,
                'volatility_5d_pct': volatility_5d,
                'volume_avg_5d': volume_avg_5d,
                'volume_ratio': float(latest['Volume'] / volume_avg_5d) if volume_avg_5d > 0 else 1.0,
                
                # Metadata
                'timestamp': datetime.now(),
                'data_quality': 'HIGH' if not hist.empty and len(hist) >= 2 else 'MEDIUM'
            }
            
            logger.debug(f"✅ {symbol} ({asset_info['name']}): ${latest['Close']:.2f} ({change_1d:+.1f}%)")
            return asset_data
            
        except Exception as e:
            logger.error(f"❌ Failed to collect data for {symbol}: {e}")
            return None
    
    def calculate_ml_indicators(self, assets_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate high-value ML indicators from collected asset data"""
        indicators = {}
        
        try:
            # Helper function to get asset price safely
            def get_price(symbol):
                return assets_data.get(symbol, {}).get('price', 0)
            
            def get_change(symbol):
                return assets_data.get(symbol, {}).get('change_1d_pct', 0)
            
            # Risk-On/Risk-Off Ratio (QQQ/VIX)
            qqq_price = get_price('QQQ')
            vix_price = get_price('^VIX')
            if qqq_price > 0 and vix_price > 0:
                indicators['risk_on_risk_off_ratio'] = {
                    'value': qqq_price / vix_price,
                    'description': 'Risk appetite indicator (higher = more risk-on)',
                    'components': {'QQQ': qqq_price, 'VIX': vix_price},
                    'ml_value': 'CRITICAL'
                }
            
            # Innovation Premium (ARKK/SPY)
            arkk_price = get_price('ARKK')
            spy_price = get_price('SPY')
            if arkk_price > 0 and spy_price > 0:
                indicators['innovation_premium'] = {
                    'value': arkk_price / spy_price,
                    'description': 'Innovation sector premium vs broad market',
                    'components': {'ARKK': arkk_price, 'SPY': spy_price},
                    'ml_value': 'HIGH'
                }
            
            # Tech Leadership (QQQ/SPY)
            if qqq_price > 0 and spy_price > 0:
                indicators['tech_leadership'] = {
                    'value': qqq_price / spy_price,
                    'description': 'Tech sector leadership vs broad market',
                    'components': {'QQQ': qqq_price, 'SPY': spy_price},
                    'ml_value': 'HIGH'
                }
            
            # Credit Spreads Proxy (HYG vs TLT daily changes)
            hyg_change = get_change('HYG')
            tlt_change = get_change('TLT')
            indicators['credit_spreads_proxy'] = {
                'value': hyg_change - tlt_change,
                'description': 'Credit spread indicator (negative = widening spreads)',
                'components': {'HYG_change': hyg_change, 'TLT_change': tlt_change},
                'ml_value': 'HIGH'
            }
            
            # Global Risk Appetite (EEM/SPY)
            eem_price = get_price('EEM')
            if eem_price > 0 and spy_price > 0:
                indicators['global_risk_appetite'] = {
                    'value': eem_price / spy_price,
                    'description': 'Emerging markets vs developed (global risk appetite)',
                    'components': {'EEM': eem_price, 'SPY': spy_price},
                    'ml_value': 'HIGH'
                }
            
            # Dollar Strength Composite
            eurusd_price = get_price('EURUSD=X')
            usdjpy_price = get_price('USDJPY=X')
            if eurusd_price > 0 and usdjpy_price > 0:
                indicators['dollar_strength_composite'] = {
                    'value': (1/eurusd_price + usdjpy_price/100) / 2,
                    'description': 'Composite dollar strength from currency pairs',
                    'components': {'EURUSD': eurusd_price, 'USDJPY': usdjpy_price},
                    'ml_value': 'MEDIUM'
                }
            
            # Volatility Regime
            move_price = get_price('^MOVE')
            if vix_price > 0 and move_price > 0:
                indicators['volatility_regime'] = {
                    'value': (vix_price + move_price) / 2,
                    'description': 'Cross-asset volatility environment',
                    'components': {'VIX': vix_price, 'MOVE': move_price},
                    'ml_value': 'HIGH'
                }
            
            logger.info(f"📊 Calculated {len(indicators)} ML indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"❌ ML indicator calculation error: {e}")
            return {}
    
    def store_market_data(self, assets_data: Dict, indicators_data: Dict) -> bool:
        """Store market data and ML indicators in macro_indicators table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()
                records_inserted = 0
                
                # Store individual asset data
                for symbol, data in assets_data.items():
                    if not data:
                        continue
                    
                    # Store main price
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, category, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), category = VALUES(category), updated_at = NOW()
                    """, (
                        f"ML_{symbol.replace('=X', '').replace('^', '')}_PRICE",
                        current_date,
                        data['price'],
                        'ML_Market_Collector',
                        data['category'],
                        datetime.now()
                    ))
                    records_inserted += 1
                    
                    # Store daily change
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, category, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), updated_at = NOW()
                    """, (
                        f"ML_{symbol.replace('=X', '').replace('^', '')}_CHANGE_1D",
                        current_date,
                        data['change_1d_pct'],
                        'ML_Market_Collector',
                        'daily_change_percent',
                        datetime.now()
                    ))
                    records_inserted += 1
                    
                    # Store volatility
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, category, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), updated_at = NOW()
                    """, (
                        f"ML_{symbol.replace('=X', '').replace('^', '')}_VOLATILITY",
                        current_date,
                        data.get('volatility_20d', 0),
                        'ML_Market_Collector',
                        'volatility_metric',
                        datetime.now()
                    ))
                    records_inserted += 1
                
                # Store calculated ML indicators
                for name, indicator in indicators_data.items():
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, indicator_date, value, data_source, category, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        value = VALUES(value), category = VALUES(category), updated_at = NOW()
                    """, (
                        f"ML_{name.upper()}",
                        current_date,
                        indicator['value'],
                        'ML_Market_Collector',
                        'ml_indicator',
                        datetime.now()
                    ))
                    records_inserted += 1
                
                # Commit transaction
                conn.commit()
                cursor.close()
                
                logger.info(f"✅ Stored {records_inserted} ML market indicators in database")
                self.collection_stats['database_writes'] += records_inserted
                return True
                
        except Exception as e:
            logger.error(f"❌ Database storage error: {e}")
            return False
    
    def collect_ml_market_data(self) -> Dict[str, Any]:
        """Main collection method for ML market data"""
        logger.info("🚀 Starting ML-focused market data collection")
        start_time = datetime.now()
        
        # Collect asset data
        assets_data = {}
        for symbol, asset_info in self.ml_assets.items():
            data = self.collect_asset_data(symbol, asset_info)
            if data:
                assets_data[symbol] = data
            
            # Rate limiting
            time.sleep(0.1)
        
        # Calculate ML indicators
        indicators_data = self.calculate_ml_indicators(assets_data)
        
        # Store in database
        storage_success = self.store_market_data(assets_data, indicators_data)
        
        # Update collection statistics
        self.collection_stats.update({
            'last_collection': datetime.now(),
            'total_collections': self.collection_stats['total_collections'] + 1,
            'assets_collected': len(assets_data),
            'ml_indicators_calculated': len(indicators_data)
        })
        
        collection_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'status': 'success' if storage_success else 'partial_failure',
            'collection_time_seconds': collection_time,
            'assets_collected': len(assets_data),
            'ml_indicators_calculated': len(indicators_data),
            'database_storage': 'success' if storage_success else 'failed',
            'timestamp': datetime.now().isoformat(),
            'total_ml_features': len(assets_data) * 3 + len(indicators_data)  # 3 metrics per asset + indicators
        }
        
        logger.info(f"✅ ML market data collection completed in {collection_time:.1f}s")
        logger.info(f"📊 Assets: {len(assets_data)}, Indicators: {len(indicators_data)}, Total ML features: {result['total_ml_features']}")
        
        return result
    
    def setup_routes(self):
        """Setup FastAPI routes for manual triggers and monitoring"""
        
        @self.app.get("/health")
        def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": "ML Market Data Collector",
                "timestamp": datetime.now().isoformat(),
                "assets_tracked": len(self.ml_assets),
                "ml_indicators": len(self.ml_calculations)
            }
        
        @self.app.get("/status")
        def get_status():
            """Get detailed collector status"""
            return {
                "service": "ML Market Data Collector",
                "status": "operational",
                "statistics": self.collection_stats,
                "configuration": {
                    "assets_tracked": len(self.ml_assets),
                    "ml_indicators": len(self.ml_calculations),
                    "shared_pool_available": SHARED_POOL_AVAILABLE
                },
                "database_pool_stats": get_pool_stats() if SHARED_POOL_AVAILABLE else "unavailable"
            }
        
        @self.app.post("/collect")
        def trigger_collection(background_tasks: BackgroundTasks):
            """Manually trigger ML market data collection"""
            background_tasks.add_task(self.collect_ml_market_data)
            return {
                "message": "ML market data collection triggered",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/assets")
        def get_tracked_assets():
            """Get list of tracked assets and their ML value"""
            return {
                "tracked_assets": self.ml_assets,
                "ml_calculations": self.ml_calculations,
                "total_features_generated": len(self.ml_assets) * 3 + len(self.ml_calculations)
            }

def main():
    """Main application entry point"""
    logger.info("🚀 Starting ML Market Data Collector Service")
    
    # Initialize collector
    collector = MLMarketDataCollector()
    
    # Setup scheduling if centralized config available
    if get_collector_schedule:
        try:
            schedule_config = get_collector_schedule("ml_market_collector")
            interval_minutes = schedule_config.get('interval_minutes', 30)
            
            schedule.every(interval_minutes).minutes.do(collector.collect_ml_market_data)
            logger.info(f"⏰ Scheduled ML market data collection every {interval_minutes} minutes")
        except Exception as e:
            logger.warning(f"Could not setup centralized scheduling: {e}. Using default.")
            schedule.every(30).minutes.do(collector.collect_ml_market_data)
            logger.info("⏰ Using default 30-minute collection schedule")
    else:
        # Default scheduling
        schedule.every(30).minutes.do(collector.collect_ml_market_data)
        logger.info("⏰ Using default 30-minute collection schedule")
    
    # Run initial collection
    logger.info("🎯 Running initial ML market data collection...")
    try:
        initial_result = collector.collect_ml_market_data()
        logger.info(f"✅ Initial collection result: {initial_result}")
    except Exception as e:
        logger.error(f"❌ Initial collection failed: {e}")
    
    # Start FastAPI server in background and run scheduler
    import threading
    
    def run_api():
        uvicorn.run(collector.app, host="0.0.0.0", port=8000, log_level="info")
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    logger.info("🌐 ML Market Data Collector API started on port 8000")
    logger.info("⏰ Starting scheduled collection loop...")
    
    # Run scheduled collections
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("👋 Shutting down ML Market Data Collector")
            break
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            time.sleep(300)  # 5 minute retry on error

if __name__ == "__main__":
    main()