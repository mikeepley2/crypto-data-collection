import mysql.connector
import logging
import time
from datetime import datetime, timedelta
import threading
from collections import defaultdict
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTimeMaterializedTableUpdater:

    def get_db_connection(self):
        """Create and return a new MySQL database connection using self.db_config."""
        return mysql.connector.connect(**self.db_config)
    def get_symbols_with_social_sentiment(self):
        """Return list of canonical symbols (from crypto_assets) that are referenced in social_sentiment_data, using robust alias/name mapping."""
        import json
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Build mapping from all possible names/aliases/symbols to canonical symbol
        cursor.execute("SELECT symbol, name, aliases FROM crypto_assets WHERE is_active=1")
        alias_map = {}  # lowercased alias/name/symbol -> canonical symbol
        active_symbols = set()
        for row in cursor.fetchall():
            symbol = row['symbol']
            active_symbols.add(symbol)
            alias_map[symbol.lower()] = symbol
            if row.get('name'):
                alias_map[row['name'].lower()] = symbol
            if row.get('aliases'):
                try:
                    aliases = json.loads(row['aliases'])
                    for alias in aliases:
                        alias_map[str(alias).lower()] = symbol
                except Exception as e:
                    logger.error(f"Error parsing aliases for {symbol}: {e}")
        # Get all unique assets from social_sentiment_data
        cursor.execute("SELECT DISTINCT asset FROM crypto_news.social_sentiment_data WHERE asset IS NOT NULL")
        sentiment_assets = set(row['asset'] for row in cursor.fetchall())
        # Map each asset to canonical symbol if possible
        matched_symbols = set()
        for asset in sentiment_assets:
            canonical = alias_map.get(asset.lower())
            if canonical:
                matched_symbols.add(canonical)
        filtered = sorted(list(matched_symbols & active_symbols))
        cursor.close()
        conn.close()
        logger.info(f"✅ Filtered to {len(filtered)} symbols present in both social_sentiment_data and crypto_assets (using alias mapping).")
        return filtered

    def calculate_price_change_24h(self, symbol, current_price, timestamp_iso):
        """Calculate 24h price change for a symbol at given timestamp"""
        try:
            if current_price is None or current_price <= 0:
                return None, None
                
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Look for price 24 hours ago (within 2 hour tolerance)
            target_time = timestamp_iso - timedelta(hours=24)
            tolerance_start = target_time - timedelta(hours=1)
            tolerance_end = target_time + timedelta(hours=1)
            
            query = """
            SELECT current_price, timestamp_iso
            FROM ml_features_materialized
            WHERE symbol = %s 
            AND timestamp_iso BETWEEN %s AND %s
            AND current_price IS NOT NULL
            AND current_price > 0
            ORDER BY ABS(TIMESTAMPDIFF(MINUTE, timestamp_iso, %s))
            LIMIT 1
            """
            
            cursor.execute(query, (symbol, tolerance_start, tolerance_end, target_time))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                # Ensure both prices are the same type to avoid Decimal/float arithmetic errors
                prev_price = float(result['current_price'])
                current_price_float = float(current_price)
                price_change = current_price_float - prev_price
                price_change_pct = (price_change / prev_price) * 100
                
                # Sanity check for extreme values (likely data errors)
                if abs(price_change_pct) > 1000:  # >1000% change is likely an error
                    logger.warning(f"Extreme price change detected for {symbol}: {price_change_pct:.2f}% - setting to null")
                    return None, None
                
                return round(price_change, 8), round(price_change_pct, 6)
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error calculating 24h price change for {symbol}: {e}")
            return None, None

    def get_latest_macro_data(self, target_date):
        """Get latest macro indicators with forward-fill for missing dates"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get the most recent macro data within 7 days
            cursor.execute("""
                SELECT indicator_name, value 
                FROM macro_indicators 
                WHERE indicator_date >= DATE_SUB(%s, INTERVAL 7 DAY)
                AND indicator_date <= %s
                ORDER BY indicator_date DESC
            """, (target_date, target_date))
            
            results = cursor.fetchall()
            macro_data = {}
            
            # Map common indicators - expanded for comprehensive macro coverage
            indicator_map = {
                'VIX': 'vix',
                'SPX': 'spx', 
                'DXY': 'dxy',
                'TNX': 'tnx',
                'FED_FUNDS_RATE': 'fed_funds_rate',
                'FEDFUNDS': 'fed_funds_rate',
                'Fed_Funds_Rate': 'fed_funds_rate',
                'TREASURY_10Y': 'treasury_10y',
                'Treasury_10Y': 'treasury_10y',
                'DGS10': 'treasury_10y',
                'Treasury_2Y': 'treasury_2y',
                'DGS2': 'treasury_2y',
                'UNEMPLOYMENT_RATE': 'unemployment_rate',
                'Unemployment_Rate': 'unemployment_rate',
                'INFLATION_RATE': 'inflation_rate',
                'Inflation_Rate': 'inflation_rate',
                'CPI': 'cpi_index',
                'Core_CPI': 'core_cpi',
                'GDP_Real': 'gdp_real',
                'GOLD_PRICE': 'gold_price',
                'GOLD': 'gold_price',
                'Gold': 'gold_price',
                'Silver': 'silver_price',
                'OIL_PRICE': 'oil_price',
                'OIL': 'oil_price',
                'WTI_Oil': 'oil_price',
                'Brent_Oil': 'brent_oil_price',
                'NASDAQ': 'nasdaq_index',
                'DOW': 'dow_jones_index',
                'DEXJPUS': 'jpy_usd_rate',
                'DEXUSEU': 'eur_usd_rate'
            }
            
            for row in results:
                indicator_name = row['indicator_name']
                if indicator_name in indicator_map:
                    field_name = indicator_map[indicator_name]
                    if field_name not in macro_data:  # Keep most recent
                        macro_data[field_name] = row['value']
            
            cursor.close()
            conn.close()
            
            return macro_data
            
        except Exception as e:
            logger.error(f"Error getting macro data: {e}")
            return {}

    def get_ors(self, symbol, timestamp, current_price):
        """Calculate basic technical indicators when missing from technical_indicators table"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get last 50 price points for calculations
            cursor.execute("""
                SELECT current_price as price FROM price_data_real 
                WHERE symbol = %s AND timestamp_iso <= %s 
                ORDER BY timestamp_iso DESC LIMIT 50
            """, (symbol, timestamp))
            prices = [row['price'] for row in cursor.fetchall()]
            
            if len(prices) < 14:
                return {}
            
            # Simple RSI calculation (14-period)
            gains = []
            losses = []
            for i in range(1, min(15, len(prices))):
                change = prices[i-1] - prices[i]  # reverse order due to DESC
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if len(gains) >= 14:
                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
            else:
                rsi = None
            
            # Simple Moving Averages
            sma_20 = sum(prices[:20]) / 20 if len(prices) >= 20 else None
            sma_50 = sum(prices[:50]) / 50 if len(prices) >= 50 else None
            
            # VWAP approximation (using current price as proxy)
            vwap = current_price  # Simplified
            
            cursor.close()
            conn.close()
            
            return {
                'rsi_14': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'vwap': vwap
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return {}

    def get_daily_ohlc_data(self, symbol, date):
        """Get daily OHLC data for a specific symbol and date (hour is ignored since OHLC is daily)"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get daily OHLC data for the date (ignore hour since OHLC is daily)
            # Use the most recent OHLC data for that day
            query = """
            SELECT 
                open_price,
                high_price,
                low_price,
                close_price,
                volume as ohlc_volume,
                data_source as ohlc_source
            FROM ohlc_data 
            WHERE symbol = %s 
            AND DATE(timestamp_iso) = %s
            ORDER BY timestamp_iso DESC
            LIMIT 1
            """
            cursor.execute(query, (symbol, date.date()))
            result = cursor.fetchone()
            
            # If no OHLC data found, try to get from price_data as fallback
            if not result:
                cursor.execute("""
                    SELECT 
                        open_24h as open_price,
                        high_24h as high_price, 
                        low_24h as low_price,
                        current_price as close_price,
                        volume_usd_24h as ohlc_volume,
                        'price_data_real_fallback' as ohlc_source
                    FROM price_data_real
                    WHERE symbol = %s AND DATE(timestamp_iso) = %s
                    ORDER BY timestamp_iso DESC LIMIT 1
                """, (symbol, date.date()))
                result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                cleaned_result = {}
                for key, value in result.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    cleaned_result[key] = value
                return cleaned_result
            return {}
        except Exception as e:
            logger.error(f"Error getting daily OHLC data for {symbol} on {date.date()}: {e}")
            return {}

    def get_macro_indicators(self, date):
        """Get macro economic indicators for a date"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT 
                MAX(CASE WHEN indicator_name = 'VIX' THEN value END) as vix,
                MAX(CASE WHEN indicator_name = 'SPX' THEN value END) as spx,
                MAX(CASE WHEN indicator_name = 'DXY' THEN value END) as dxy,
                MAX(CASE WHEN indicator_name = 'TNX' THEN value END) as tnx,
                MAX(CASE WHEN indicator_name = 'FEDFUNDS' THEN value END) as fed_funds_rate,
                MAX(CASE WHEN indicator_name = 'Fed_Funds_Rate' THEN value END) as fed_funds_rate_alt,
                MAX(CASE WHEN indicator_name = 'Gold' THEN value END) as gold_price,
                MAX(CASE WHEN indicator_name = 'WTI_Oil' THEN value END) as oil_price,
                MAX(CASE WHEN indicator_name = 'Inflation_Rate' THEN value END) as inflation_rate,
                MAX(CASE WHEN indicator_name = 'Treasury_10Y' THEN value END) as treasury_10y,
                MAX(CASE WHEN indicator_name = 'Treasury_2Y' THEN value END) as treasury_2y
            FROM crypto_prices.macro_indicators 
            WHERE indicator_date = %s
            """
            cursor.execute(query, (date.date(),))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                cleaned_result = {}
                for key, value in result.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    # Combine fed_funds_rate fields
                    if key == 'fed_funds_rate_alt' and value and not cleaned_result.get('fed_funds_rate'):
                        cleaned_result['fed_funds_rate'] = value
                    elif key != 'fed_funds_rate_alt':
                        cleaned_result[key] = value
                return cleaned_result
            return {}
        except Exception as e:
            logger.error(f"Error getting macro indicators: {e}")
            return {}

    def get_crypto_sentiment(self, date):
        """Get crypto sentiment data for a date"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT 
                COUNT(*) as sentiment_count,
                AVG(cryptobert_score) as avg_cryptobert_score,
                AVG(vader_score) as avg_vader_score,
                AVG(textblob_score) as avg_textblob_score,
                AVG(crypto_keywords_score) as avg_crypto_keywords_score
            FROM crypto_news.crypto_sentiment_data 
            WHERE DATE(published_at) = %s
            AND published_at IS NOT NULL
            """
            cursor.execute(query, (date.date(),))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                cleaned_result = {}
                for key, value in result.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    cleaned_result[key] = value
                return cleaned_result
            return {}
        except Exception as e:
            logger.error(f"Error getting crypto sentiment: {e}")
            return {}

    def get_stock_sentiment(self, date):
        """Get stock market sentiment data for a date"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT 
                COUNT(*) as sentiment_count,
                AVG(sentiment_score) as avg_finbert_sentiment_score,
                AVG(confidence) as avg_fear_greed_score,
                AVG(sentiment_score) as avg_volatility_sentiment,
                AVG(confidence) as avg_risk_appetite,
                AVG(sentiment_score) as avg_crypto_correlation
            FROM crypto_news.stock_sentiment_data 
            WHERE DATE(timestamp) = %s
            AND timestamp IS NOT NULL
            """
            cursor.execute(query, (date.date(),))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result:
                cleaned_result = {}
                for key, value in result.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    cleaned_result[key] = value
                return cleaned_result
            return {}
        except Exception as e:
            logger.error(f"Error getting stock sentiment: {e}")
            return {}

    def get_advanced_sentiment_data(self, symbol, target_date):
        """Get comprehensive sentiment data from real_time_sentiment_signals and sentiment_aggregation"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            sentiment_data = {}
            
            # Get sentiment aggregation data for the symbol
            cursor.execute("""
                SELECT 
                    composite_sentiment,
                    confidence_score,
                    signal_strength,
                    news_sentiment,
                    news_count,
                    social_sentiment,
                    social_count,
                    weighted_sentiment,
                    sentiment_momentum,
                    volatility as sentiment_volatility,
                    data_quality_score,
                    source_diversity
                FROM sentiment_aggregation
                WHERE symbol = %s 
                AND DATE(timestamp) = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol, target_date))
            
            agg_result = cursor.fetchone()
            if agg_result:
                # Map aggregation data to ml_features fields with existing column names
                if agg_result['composite_sentiment'] is not None:
                    sentiment_data['social_posts'] = agg_result['composite_sentiment']  # Use existing field
                    sentiment_data['social_sentiment_score'] = agg_result['composite_sentiment']
                    
                if agg_result['confidence_score'] is not None:
                    sentiment_data['social_confidence'] = agg_result['confidence_score']
                    
                if agg_result['signal_strength'] is not None:
                    sentiment_data['sentiment_strength'] = agg_result['signal_strength']
                    
                if agg_result['news_sentiment'] is not None:
                    sentiment_data['news_sentiment'] = agg_result['news_sentiment']
                    
                if agg_result['news_count'] is not None:
                    sentiment_data['news_volume'] = agg_result['news_count']
                    
                if agg_result['social_sentiment'] is not None:
                    sentiment_data['social_avg_sentiment'] = agg_result['social_sentiment']
                    
                if agg_result['social_count'] is not None:
                    sentiment_data['social_post_count'] = agg_result['social_count']
                    
                if agg_result['weighted_sentiment'] is not None:
                    sentiment_data['weighted_sentiment'] = agg_result['weighted_sentiment']
                    
                if agg_result['sentiment_momentum'] is not None:
                    sentiment_data['sentiment_momentum'] = agg_result['sentiment_momentum']
                    
                if agg_result['sentiment_volatility'] is not None:
                    sentiment_data['sentiment_volatility'] = agg_result['sentiment_volatility']
                    
                if agg_result['data_quality_score'] is not None:
                    sentiment_data['data_quality_score'] = agg_result['data_quality_score']
                    
                if agg_result['source_diversity'] is not None:
                    sentiment_data['source_diversity'] = agg_result['source_diversity']
            
            # Get real-time sentiment signals for additional metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as signal_count,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(confidence) as avg_confidence,
                    AVG(signal_strength) as avg_strength,
                    COUNT(DISTINCT signal_type) as signal_types,
                    MAX(timestamp) as latest_signal
                FROM real_time_sentiment_signals
                WHERE symbol = %s 
                AND DATE(timestamp) = %s
            """, (symbol, target_date))
            
            rt_result = cursor.fetchone()
            if rt_result and rt_result['signal_count'] > 0:
                # Map real-time signals to available fields
                if rt_result['signal_count'] is not None:
                    sentiment_data['realtime_signals'] = rt_result['signal_count']
                    
                if rt_result['avg_sentiment'] is not None:
                    sentiment_data['realtime_sentiment'] = rt_result['avg_sentiment']
                    
                if rt_result['avg_confidence'] is not None:
                    sentiment_data['realtime_confidence'] = rt_result['avg_confidence']
                    
                if rt_result['avg_strength'] is not None:
                    sentiment_data['realtime_strength'] = rt_result['avg_strength']
                    
                if rt_result['signal_types'] is not None:
                    sentiment_data['signal_types'] = rt_result['signal_types']
            
            cursor.close()
            conn.close()
            
            logger.info(f"📊 {symbol}: Retrieved {len(sentiment_data)} advanced sentiment fields for {target_date}")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error getting advanced sentiment data for {symbol}: {e}")
            return {}

    def force_fresh_technical_indicators(self, symbol, days_back=3):
        """Force generation of fresh technical indicators via service call"""
        try:
            import requests
            
            # Technical indicators service endpoint
            tech_service_url = "http://technical-indicators.crypto-collectors.svc.cluster.local:8000"
            
            logger.info(f"🔧 Forcing fresh technical indicators for {symbol}...")
            
            # Call the service to generate fresh indicators
            response = requests.post(f"{tech_service_url}/calculate/{symbol}",
                                   json={"force_recalculate": True, "days_back": days_back},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                records_created = result.get('records_created', 0)
                logger.info(f"✅ {symbol}: Generated {records_created} fresh technical indicator records")
                return True
            else:
                logger.warning(f"⚠️ {symbol}: Technical indicators service returned {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error forcing fresh technical indicators for {symbol}: {e}")
            return False
    
    def get_enhanced_technical_indicators(self, symbol, timestamp, force_fresh=False):
        """Get comprehensive technical indicators with optional fresh generation"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # First, try to get existing recent data
            cursor.execute("""
                SELECT 
                    rsi_14, sma_20, sma_50, sma_200, ema_12, ema_26, ema_50,
                    macd_line, macd_signal, macd_histogram,
                    bb_upper, bb_middle, bb_lower, bb_width,
                    stoch_k, stoch_d, williams_r,
                    atr_14, adx, cci, momentum, roc,
                    vwap, obv, mfi, tsi, ultimate_oscillator,
                    sar, volume_sma, volatility,
                    candlestick_pattern, trend_strength, price_velocity
                FROM technical_indicators
                WHERE symbol = %s 
                AND timestamp <= %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol, timestamp))
            
            tech_data = cursor.fetchone()
            
            # Check data freshness and completeness
            needs_fresh_data = False
            if not tech_data:
                needs_fresh_data = True
                logger.info(f"📊 {symbol}: No technical indicators found, will generate fresh data")
            else:
                # Check if key indicators are missing
                key_indicators = ['rsi_14', 'sma_20', 'macd_line', 'bb_upper', 'atr_14']
                missing_indicators = [ind for ind in key_indicators if tech_data.get(ind) is None]
                if len(missing_indicators) > 2:  # If more than 2 key indicators are missing
                    needs_fresh_data = True
                    logger.info(f"📊 {symbol}: Missing key indicators {missing_indicators}, will generate fresh data")
            
            # Force fresh data generation if needed or requested
            if (needs_fresh_data or force_fresh) and not getattr(self, '_fresh_tech_attempted', set()).__contains__(symbol):
                # Mark as attempted to avoid infinite loops
                if not hasattr(self, '_fresh_tech_attempted'):
                    self._fresh_tech_attempted = set()
                self._fresh_tech_attempted.add(symbol)
                
                # Generate fresh technical indicators
                if self.force_fresh_technical_indicators(symbol):
                    # Wait a moment for data to be available
                    import time
                    time.sleep(2)
                    
                    # Re-query for fresh data
                    cursor.execute("""
                        SELECT 
                            rsi_14, sma_20, sma_50, sma_200, ema_12, ema_26, ema_50,
                            macd_line, macd_signal, macd_histogram,
                            bb_upper, bb_middle, bb_lower, bb_width,
                            stoch_k, stoch_d, williams_r,
                            atr_14, adx, cci, momentum, roc,
                            vwap, obv, mfi, tsi, ultimate_oscillator,
                            sar, volume_sma, volatility,
                            candlestick_pattern, trend_strength, price_velocity
                        FROM technical_indicators
                        WHERE symbol = %s 
                        AND timestamp <= %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (symbol, timestamp))
                    
                    fresh_tech_data = cursor.fetchone()
                    if fresh_tech_data:
                        tech_data = fresh_tech_data
                        logger.info(f"✅ {symbol}: Retrieved fresh technical indicators")
            
            cursor.close()
            conn.close()
            
            # Return the technical data (could be None if no data available)
            return tech_data or {}
            
        except Exception as e:
            logger.error(f"Error getting enhanced technical indicators for {symbol}: {e}")
            return {}

    def calculate_data_quality_score(self, record):
        """Calculate data quality score based on available features"""
        score = 0
        # Core price data (40 points)
        if record.get('current_price'):
            score += 15
        if record.get('volume_24h') or record.get('volume_usd_24h') or record.get('volume_qty_24h'):
            score += 15
        # OHLC data (10 points)
        if record.get('open_price') and record.get('high_price') and record.get('low_price') and record.get('close_price'):
            score += 10
        # Technical indicators (40 points)
        if record.get('rsi_14'):
            score += 10
        if record.get('sma_20'):
            score += 10
        if record.get('ema_12'):
            score += 10
        if record.get('macd_line'):
            score += 10
        # Sentiment data (30 points) - Enhanced for advanced sentiment
        sentiment_score = 0
        if record.get('avg_cryptobert_score'):
            sentiment_score += 5
        if record.get('avg_finbert_sentiment_score'):
            sentiment_score += 5
        if record.get('social_sentiment_score'):
            sentiment_score += 5
        if record.get('news_sentiment'):
            sentiment_score += 5
        if record.get('social_post_count'):
            sentiment_score += 5
        if record.get('realtime_sentiment'):
            sentiment_score += 5
        score += sentiment_score
        return round(score, 2)

    def calculate_missing_technical_indicators(self, symbol, timestamp, current_price):
        """Calculate basic technical indicators when missing from technical_indicators table"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get last 50 price points for calculations
            cursor.execute("""
                SELECT current_price as price FROM price_data_real 
                WHERE symbol = %s AND timestamp_iso <= %s 
                ORDER BY timestamp_iso DESC LIMIT 50
            """, (symbol, timestamp))
            prices = [float(row['price']) for row in cursor.fetchall()]
            
            if len(prices) < 14:
                return {}
            
            # Simple RSI calculation (14-period)
            gains, losses = [], []
            for i in range(1, min(15, len(prices))):
                change = prices[i-1] - prices[i]  # reverse order due to DESC
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if len(gains) >= 14:
                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                else:
                    rsi = 100
            else:
                rsi = None
            
            # Simple Moving Averages
            sma_20 = sum(prices[:20]) / 20 if len(prices) >= 20 else None
            sma_50 = sum(prices[:50]) / 50 if len(prices) >= 50 else None
            
            # EMA calculations (12 and 26 period)
            ema_12 = self.calculate_ema(prices, 12) if len(prices) >= 12 else None
            ema_26 = self.calculate_ema(prices, 26) if len(prices) >= 26 else None
            
            # VWAP approximation (using current price as proxy)
            vwap = float(current_price)
            
            # ATR approximation
            atr_14 = (max(prices[:14]) - min(prices[:14])) if len(prices) >= 14 else None
            
            cursor.close()
            conn.close()
            
            indicators = {
                'rsi_14': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'ema_12': ema_12,
                'ema_26': ema_26,
                'vwap': vwap,
                'atr_14': atr_14
            }
            
            # Calculate MACD if we have both EMAs
            if ema_12 and ema_26:
                indicators['macd_line'] = ema_12 - ema_26
                indicators['macd_signal'] = indicators['macd_line'] * 0.9  # Simple approximation
                indicators['macd_histogram'] = indicators['macd_line'] - indicators['macd_signal']
            
            logger.info(f"🧮 Calculated {len([v for v in indicators.values() if v is not None])} technical indicators for {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")
            return {}

    def calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        # Start with SMA for first EMA value
        sma = sum(prices[-period:]) / period
        ema = sma
        
        # Calculate EMA for remaining values
        multiplier = 2 / (period + 1)
        for i in range(len(prices) - period - 1, -1, -1):  # Work backwards through prices
            ema = (prices[i] * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def insert_or_update_record(self, record, conn=None, cursor=None):
        """Insert or update a single record in ml_features_materialized only if new values fill missing fields. Accepts optional conn/cursor for batch processing."""
        own_conn = False
        own_cursor = False
        try:
            if conn is None:
                conn = self.get_db_connection()
                own_conn = True
            if cursor is None:
                cursor = conn.cursor(dictionary=True, buffered=True)
                own_cursor = True
            select_sql = """
            SELECT * FROM ml_features_materialized WHERE symbol = %s AND price_date = %s AND price_hour = %s
            """
            cursor.execute(select_sql, (record['symbol'], record['price_date'], record['price_hour']))
            existing = cursor.fetchone()
            if not existing:
                if own_cursor:
                    cursor.close()
                cursor2 = conn.cursor()
                record['data_quality_score'] = self.calculate_data_quality_score(record)
                required_fields = [
                    'rsi_14', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
                    'macd_line', 'macd_signal', 'macd_histogram',
                    'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 'atr_14', 'vwap',
                    'vix', 'spx', 'dxy', 'tnx', 'fed_funds_rate',
                    'crypto_sentiment_count', 'avg_cryptobert_score', 'avg_vader_score',
                    'avg_textblob_score', 'avg_crypto_keywords_score',
                    'stock_sentiment_count', 'avg_finbert_sentiment_score',
                    'avg_fear_greed_score', 'avg_volatility_sentiment',
                    'avg_risk_appetite', 'avg_crypto_correlation',
                    'general_crypto_sentiment_count', 'avg_general_cryptobert_score',
                    'avg_general_vader_score', 'avg_general_textblob_score', 'avg_general_crypto_keywords_score',
                    # Social sentiment fields
                    'social_post_count', 'social_avg_sentiment', 'social_weighted_sentiment',
                    'social_engagement_weighted_sentiment', 'social_verified_user_sentiment',
                    'social_total_engagement', 'social_unique_authors', 'social_avg_confidence',
                    # OHLC fields that are used in INSERT statement but were missing from required_fields
                    'open_price', 'high_price', 'low_price', 'close_price', 'ohlc_source', 'ohlc_volume'
                ]
                for field in required_fields:
                    if field not in record:
                        record[field] = None
                if record.get('crypto_sentiment_count') is None:
                    record['crypto_sentiment_count'] = 0
                if record.get('stock_sentiment_count') is None:
                    record['stock_sentiment_count'] = 0
                insert_sql = """
                INSERT INTO ml_features_materialized (
                    symbol, price_date, price_hour, timestamp_iso,
                    current_price, volume_24h, hourly_volume, market_cap,
                    price_change_24h, price_change_percentage_24h,
                    open_price, high_price, low_price, close_price, ohlc_volume, ohlc_source,
                    rsi_14, sma_20, sma_50, ema_12, ema_26,
                    macd_line, macd_signal, macd_histogram,
                    bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap,
                    vix, spx, dxy, tnx, fed_funds_rate,
                    crypto_sentiment_count, avg_cryptobert_score, avg_vader_score,
                    avg_textblob_score, avg_crypto_keywords_score,
                    stock_sentiment_count, avg_finbert_sentiment_score,
                    avg_fear_greed_score, avg_volatility_sentiment,
                    avg_risk_appetite, avg_crypto_correlation,
                    general_crypto_sentiment_count, avg_general_cryptobert_score,
                    avg_general_vader_score, avg_general_textblob_score, avg_general_crypto_keywords_score,
                    social_post_count, social_avg_sentiment, social_weighted_sentiment,
                    social_engagement_weighted_sentiment, social_verified_user_sentiment,
                    social_total_engagement, social_unique_authors, social_avg_confidence,
                    data_quality_score
                ) VALUES (
                    %(symbol)s, %(price_date)s, %(price_hour)s, %(timestamp_iso)s,
                    %(current_price)s, %(volume_24h)s, %(hourly_volume)s, %(market_cap)s,
                    %(price_change_24h)s, %(price_change_percentage_24h)s,
                    %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, %(ohlc_volume)s, %(ohlc_source)s,
                    %(rsi_14)s, %(sma_20)s, %(sma_50)s, %(ema_12)s, %(ema_26)s,
                    %(macd_line)s, %(macd_signal)s, %(macd_histogram)s,
                    %(bb_upper)s, %(bb_middle)s, %(bb_lower)s, %(stoch_k)s, %(stoch_d)s, %(atr_14)s, %(vwap)s,
                    %(vix)s, %(spx)s, %(dxy)s, %(tnx)s, %(fed_funds_rate)s,
                    %(crypto_sentiment_count)s, %(avg_cryptobert_score)s, %(avg_vader_score)s,
                    %(avg_textblob_score)s, %(avg_crypto_keywords_score)s,
                    %(stock_sentiment_count)s, %(avg_finbert_sentiment_score)s,
                    %(avg_fear_greed_score)s, %(avg_volatility_sentiment)s,
                    %(avg_risk_appetite)s, %(avg_crypto_correlation)s,
                    %(general_crypto_sentiment_count)s, %(avg_general_cryptobert_score)s,
                    %(avg_general_vader_score)s, %(avg_general_textblob_score)s, %(avg_general_crypto_keywords_score)s,
                    %(social_post_count)s, %(social_avg_sentiment)s, %(social_weighted_sentiment)s,
                    %(social_engagement_weighted_sentiment)s, %(social_verified_user_sentiment)s,
                    %(social_total_engagement)s, %(social_unique_authors)s, %(social_avg_confidence)s,
                    %(data_quality_score)s
                )
                """
                # logger.debug(f"SQL: {insert_sql}")
                # logger.debug(f"PARAMS: {record}")
                cursor2.execute(insert_sql, record)
                # logger.debug(f"Affected rows: {affected}")
                self.processing_stats['total_inserted'] += 1
                cursor2.close()
                if own_conn:
                    conn.close()
                return "INSERTED"
            update_fields = {}
            # Always check and update social sentiment fields if they differ
            social_fields = [
                'social_post_count', 'social_avg_sentiment', 'social_avg_confidence', 'social_unique_authors'
            ]
            # Also always update OHLC fields if they differ or are missing
            ohlc_fields = [
                'open_price', 'high_price', 'low_price', 'close_price', 'ohlc_source'
            ]
            for key, value in record.items():
                if key in existing:
                    if (existing[key] is None and value is not None) or \
                       (key in social_fields and value != existing[key]) or \
                       (key in ohlc_fields and value != existing[key]):
                        update_fields[key] = value
            if update_fields:
                set_clause = ', '.join([f"{k} = %s" for k in update_fields.keys()])
                update_sql = f"UPDATE ml_features_materialized SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE symbol = %s AND price_date = %s AND price_hour = %s"
                params = list(update_fields.values()) + [record['symbol'], record['price_date'], record['price_hour']]
                cursor2 = conn.cursor()
                cursor2.execute(update_sql, params)
                affected = cursor2.rowcount
                self.processing_stats['total_updated'] += 1
                cursor2.close()
                if own_conn:
                    conn.close()
                return "UPDATED"
            else:
                if own_conn:
                    conn.close()
                return "SKIPPED"
        except Exception as e:
            import traceback
            logger.error(f"Error in insert_or_update_record: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Record symbol: {record.get('symbol', 'unknown')}")
            logger.error(f"Record timestamp: {record.get('timestamp_iso', 'unknown')}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if own_conn:
                conn.close()
            return "ERROR"


    def get_new_price_data(self, symbol, since_timestamp, end_date):
        """Get new price data since the last processed timestamp, up to end_date, using new volume columns"""
        try:
            import os
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            min_time = since_timestamp
            max_time = None
            if end_date:
                max_time = datetime.combine(end_date, datetime.max.time())
            
            # Use environment variables for column mapping if available
            source_timestamp_col = os.getenv('SOURCE_TIMESTAMP_COLUMN', 'timestamp_iso')
            current_price_col = os.getenv('CURRENT_PRICE_COLUMN', 'current_price')
            volume_col = os.getenv('VOLUME_COLUMN', 'volume_usd_24h')
            price_change_24h_col = os.getenv('PRICE_CHANGE_24H_COLUMN', 'price_change_24h')
            percent_change_24h_col = os.getenv('PERCENT_CHANGE_24H_COLUMN', 'price_change_percentage_24h')
            
            query = f"""
            SELECT 
                symbol, {source_timestamp_col} as timestamp_iso, {current_price_col} as current_price, 
                open_24h as open, high_24h as high, low_24h as low, current_price as close, volume_usd_24h as volume,
                market_cap, {price_change_24h_col} as price_change_24h, 
                {percent_change_24h_col} as price_change_percentage_24h
            FROM price_data_real 
            WHERE symbol = %s 
            AND {source_timestamp_col} >= %s
            """
            params = [symbol, min_time]
            if max_time:
                query += f" AND {source_timestamp_col} <= %s"
                params.append(max_time)
            query += f" AND {current_price_col} IS NOT NULL ORDER BY {source_timestamp_col} ASC"
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            cleaned_results = []
            for result in results:
                cleaned_result = {}
                for key, value in result.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    cleaned_result[key] = value
                cleaned_results.append(cleaned_result)
            return cleaned_results
        except Exception as e:
            logger.error(f"Error getting new price data for {symbol}: {e}")
            return []
    def process_symbol_updates(self, symbol):
        """Process updates for a single symbol, batching existing records for speed"""
        logger.info(f"Starting processing for symbol: {symbol}")
        start_time = getattr(self, 'start_date', (datetime.now() - timedelta(days=7)).date())
        end_time = getattr(self, 'end_date', datetime.now().date())
        start_dt = datetime.combine(start_time, datetime.min.time())
        new_price_data = []
        try:
            new_price_data = self.get_new_price_data(symbol, start_dt, end_time)
        except Exception as e:
            logger.error(f"Error fetching new price data for {symbol}: {e}")
        logger.info(f"{symbol}: Found {len(new_price_data)} new records from {start_time} to {end_time}")
        if not new_price_data:
            logger.info(f"🏁 Finished processing for symbol: {symbol}")
            return 0
        # Batch fetch all existing records for this symbol/date range
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            select_sql = """
            SELECT * FROM ml_features_materialized WHERE symbol = %s AND price_date >= %s AND price_date <= %s
            """
            cursor.execute(select_sql, (symbol, start_time, end_time))
            existing_records = cursor.fetchall()
            existing_lookup = {(r['price_date'], r['price_hour']): r for r in existing_records}
        except Exception as e:
            logger.error(f"Error batch fetching existing records for {symbol}: {e}")
            if 'conn' in locals():
                cursor.close()
                conn.close()
            existing_lookup = {}
            return 0
        processed_count = 0
        from collections import defaultdict
        hourly_records = defaultdict(list)
        for price_record in new_price_data:
            timestamp_iso = price_record['timestamp_iso']
            hour_key = (timestamp_iso.date(), timestamp_iso.hour)
            hourly_records[hour_key].append(price_record)
        logger.info(f"{symbol}: Grouped into {len(hourly_records)} hourly records")
        # Batch fetch all technical indicators for this symbol/date range
        tech_lookup = {}
        try:
            tech_conn = self.get_db_connection()
            tech_cursor = tech_conn.cursor(dictionary=True)
            tech_query = """
            SELECT 
                symbol, timestamp,
                rsi_14, sma_20, sma_50, ema_12, ema_26,
                macd_line, macd_signal, macd_histogram,
                bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap
            FROM technical_indicators 
            WHERE symbol = %s 
            AND DATE(timestamp) >= %s AND DATE(timestamp) <= %s
            """
            tech_cursor.execute(tech_query, (symbol, start_time, end_time))
            for row in tech_cursor.fetchall():
                if row['timestamp']:  # Check if timestamp is not None
                    key = (row['timestamp'].date(), row['timestamp'].hour)
                    tech_lookup[key] = row
            tech_cursor.close()
            tech_conn.close()
        except Exception as e:
            logger.error(f"Error batch fetching technical indicators for {symbol}: {e}")

        # Batch fetch macro indicators for the date range
        macro_lookup = {}
        try:
            macro_conn = self.get_db_connection()
            macro_cursor = macro_conn.cursor(dictionary=True)
            macro_query = """
            SELECT DISTINCT
                indicator_name,
                value,
                indicator_date
            FROM macro_indicators 
            WHERE indicator_name IN ('VIX', 'SPX', 'DXY', 'Treasury_10Y', 'Fed_Funds_Rate', 'DGS10', 'FEDFUNDS')
            AND indicator_date >= %s AND indicator_date <= %s
            ORDER BY indicator_name, indicator_date DESC
            """
            macro_cursor.execute(macro_query, (start_time, end_time))
            # Build macro lookup with forward-fill logic
            macro_data = {}
            for row in macro_cursor.fetchall():
                indicator = row['indicator_name']
                date = row['indicator_date']
                value = row['value']
                
                # Map indicator names to our column names
                col_mapping = {
                    'VIX': 'vix',
                    'SPX': 'spx', 
                    'DXY': 'dxy',
                    'Treasury_10Y': 'tnx',
                    'Fed_Funds_Rate': 'fed_funds_rate',
                    'DGS10': 'tnx',  # Use DGS10 as fallback for Treasury 10Y
                    'FEDFUNDS': 'fed_funds_rate'  # Use FEDFUNDS as fallback for Fed Funds
                }
                
                if indicator in col_mapping:
                    col_name = col_mapping[indicator]
                    if date not in macro_data:
                        macro_data[date] = {}
                    macro_data[date][col_name] = value
                    
            # Create hourly lookup with forward-fill for each day
            for date_key in macro_data:
                for hour in range(24):
                    key = (date_key, hour)
                    macro_lookup[key] = macro_data[date_key]
                    
            macro_cursor.close()
            macro_conn.close()
        except Exception as e:
            logger.error(f"Error batch fetching macro indicators: {e}")

        # Batch fetch coin-specific and general crypto sentiment for the date range
        coin_sent_lookup = {}
        general_sent_lookup = {}
        try:
            crypto_conn = self.get_db_connection()
            crypto_cursor = crypto_conn.cursor(dictionary=True)
            # Coin-specific sentiment
            coin_query = """
            SELECT 
                asset, DATE(published_at) as sent_date, HOUR(published_at) as sent_hour,
                COUNT(*) as sentiment_count,
                AVG(cryptobert_score) as avg_cryptobert_score,
                AVG(vader_score) as avg_vader_score,
                AVG(textblob_score) as avg_textblob_score,
                AVG(crypto_keywords_score) as avg_crypto_keywords_score
            FROM crypto_news.crypto_sentiment_data 
            WHERE DATE(published_at) >= %s AND DATE(published_at) <= %s
            AND published_at IS NOT NULL
            AND asset IS NOT NULL AND asset != 'crypto_general'
            GROUP BY asset, sent_date, sent_hour
            """
            crypto_cursor.execute(coin_query, (start_time, end_time))
            for row in crypto_cursor.fetchall():
                key = (row['asset'], row['sent_date'], row['sent_hour'])
                coin_sent_lookup[key] = row
            # General crypto sentiment
            general_query = """
            SELECT 
                DATE(published_at) as sent_date, HOUR(published_at) as sent_hour,
                COUNT(*) as sentiment_count,
                AVG(cryptobert_score) as avg_cryptobert_score,
                AVG(vader_score) as avg_vader_score,
                AVG(textblob_score) as avg_textblob_score,
                AVG(crypto_keywords_score) as avg_crypto_keywords_score
            FROM crypto_news.crypto_sentiment_data 
            WHERE DATE(published_at) >= %s AND DATE(published_at) <= %s
            AND published_at IS NOT NULL
            AND asset = 'crypto_general'
            GROUP BY sent_date, sent_hour
            """
            crypto_cursor.execute(general_query, (start_time, end_time))
            for row in crypto_cursor.fetchall():
                key = (row['sent_date'], row['sent_hour'])
                general_sent_lookup[key] = row
            # Social sentiment (from social_sentiment_data)
            social_sent_lookup = {}
            # Fetch aliases and name for this symbol from crypto_assets
            asset_conn = self.get_db_connection()
            asset_cursor = asset_conn.cursor(dictionary=True)
            asset_cursor.execute("SELECT symbol, name, aliases FROM crypto_assets WHERE symbol = %s", (symbol,))
            asset_row = asset_cursor.fetchone()
            asset_cursor.close()
            asset_conn.close()
            sentiment_assets = set()
            alias_to_canonical = {}
            if asset_row:
                sentiment_assets.add(asset_row['symbol'].lower())
                alias_to_canonical[asset_row['symbol'].lower()] = symbol
                if asset_row['name']:
                    sentiment_assets.add(asset_row['name'].lower())
                    alias_to_canonical[asset_row['name'].lower()] = symbol
                if asset_row['aliases']:
                    import json
                    try:
                        aliases = json.loads(asset_row['aliases'])
                        for alias in aliases:
                            sentiment_assets.add(str(alias).lower())
                            alias_to_canonical[str(alias).lower()] = symbol
                    except Exception as e:
                        logger.error(f"Error parsing aliases for {symbol}: {e}")
            else:
                sentiment_assets.add(symbol.lower())
                alias_to_canonical[symbol.lower()] = symbol
            sentiment_assets = [a.lower() for a in sentiment_assets]
            logger.info(f"🔎 {symbol}: Sentiment asset aliases used for matching: {sentiment_assets}")
            # Print to console for ETH and BTC
            if symbol in ("ETH", "BTC"):
                print(f"\n[DEBUG] {symbol}: Sentiment asset aliases used for matching: {sentiment_assets}")
            # DEBUG: Print unique asset values in social_sentiment_data for this date range
            try:
                debug_conn = self.get_db_connection()
                debug_cursor = debug_conn.cursor()
                debug_cursor.execute(
                    "SELECT DISTINCT asset FROM crypto_news.social_sentiment_data WHERE DATE(timestamp) >= %s AND DATE(timestamp) <= %s",
                    (start_time, end_time)
                )
                unique_assets = [row[0] for row in debug_cursor.fetchall()]
                logger.info(f"🔎 {symbol}: Unique assets in social_sentiment_data for date range: {unique_assets}")
                if symbol in ("ETH", "BTC"):
                    print(f"[DEBUG] {symbol}: Unique assets in social_sentiment_data for date range: {unique_assets}")
                    # Print diff
                    missing = set(sentiment_assets) - set([a.lower() for a in unique_assets if a])
                    extra = set([a.lower() for a in unique_assets if a]) - set(sentiment_assets)
                    print(f"[DEBUG] {symbol}: Aliases missing from unique_assets: {missing}")
                    print(f"[DEBUG] {symbol}: Unique_assets not in aliases: {extra}")
                debug_cursor.close()
                debug_conn.close()
            except Exception as e:
                logger.error(f"Error fetching unique assets for debug: {e}")
                if symbol in ("ETH", "BTC"):
                    print(f"[DEBUG] {symbol}: Error fetching unique assets for debug: {e}")
            format_strings = ','.join(['%s'] * len(sentiment_assets))
            # Use LOWER(asset) for case-insensitive matching
            social_query = f"""
            SELECT
                DATE(timestamp) AS price_date,
                HOUR(timestamp) AS price_hour,
                COUNT(*) AS social_post_count,
                AVG(sentiment_score) AS social_avg_sentiment,
                AVG(confidence) AS social_avg_confidence,
                COUNT(DISTINCT author) AS social_unique_authors
            FROM crypto_news.social_sentiment_data
            WHERE LOWER(asset) IN ({format_strings}) AND timestamp IS NOT NULL
                AND DATE(timestamp) >= %s AND DATE(timestamp) <= %s
            GROUP BY price_date, price_hour
            """
            if symbol in ("ETH", "BTC"):
                print(f"[DEBUG] {symbol}: Running social sentiment query: {social_query}")
                print(f"[DEBUG] {symbol}: Query params: {(*sentiment_assets, start_time, end_time)}")
            logger.info(f"🔎 {symbol}: Running social sentiment query with aliases: {sentiment_assets}")
            crypto_cursor.execute(social_query, (*sentiment_assets, start_time, end_time))
            found_any = False
            for row in crypto_cursor.fetchall():
                found_any = True
                key = (symbol, row['price_date'], row['price_hour'])
                social_sent_lookup[key] = {
                    'social_post_count': row['social_post_count'],
                    'social_avg_sentiment': row['social_avg_sentiment'],
                    'social_avg_confidence': row['social_avg_confidence'],
                    'social_unique_authors': row['social_unique_authors']
                }
            if not found_any:
                logger.info(f"🔎 {symbol}: No social sentiment records found for any aliases in this date range.")
            crypto_cursor.close()
            crypto_conn.close()
        except Exception as e:
            logger.error(f"Error batch fetching crypto sentiment: {e}")

        # Batch fetch stock sentiment for the date range
        stock_sent_lookup = {}
        try:
            stock_conn = self.get_db_connection()
            stock_cursor = stock_conn.cursor(dictionary=True)
            stock_query = """
            SELECT 
                DATE(timestamp) as sent_date, HOUR(timestamp) as sent_hour,
                COUNT(*) as sentiment_count,
                AVG(sentiment_score) as avg_finbert_sentiment_score,
                AVG(confidence) as avg_fear_greed_score,
                AVG(sentiment_score) as avg_volatility_sentiment,
                AVG(confidence) as avg_risk_appetite,
                AVG(sentiment_score) as avg_crypto_correlation
            FROM crypto_news.stock_sentiment_data 
            WHERE DATE(timestamp) >= %s AND DATE(timestamp) <= %s
            AND timestamp IS NOT NULL
            GROUP BY sent_date, sent_hour
            """
            stock_cursor.execute(stock_query, (start_time, end_time))
            for row in stock_cursor.fetchall():
                key = (row['sent_date'], row['sent_hour'])
                stock_sent_lookup[key] = row
            stock_cursor.close()
            stock_conn.close()
        except Exception as e:
            logger.error(f"Error batch fetching stock sentiment: {e}")
        # Open a single connection/cursor for all per-record updates
        update_cursor = conn.cursor(dictionary=True, buffered=True)
        for hour_key, records in hourly_records.items():
            price_record = max(records, key=lambda r: r['timestamp_iso'])
            try:
                timestamp_iso = price_record['timestamp_iso']
                # Only use USD volumes, calculate from qty*price if needed, else null
                volume_usd_24h = price_record.get('volume_usd_24h')
                volume_qty_24h = price_record.get('volume_qty_24h')
                current_price = price_record.get('current_price')
                if volume_usd_24h is not None and volume_usd_24h != 0:
                    volume_24h = volume_usd_24h
                elif volume_qty_24h is not None and current_price is not None:
                    volume_24h = volume_qty_24h * current_price
                else:
                    volume_24h = None

                hourly_volume_usd = price_record.get('hourly_volume_usd')
                hourly_volume_qty = price_record.get('hourly_volume_qty')
                if hourly_volume_usd is not None and hourly_volume_usd != 0:
                    hourly_volume = hourly_volume_usd
                elif hourly_volume_qty is not None and current_price is not None:
                    hourly_volume = hourly_volume_qty * current_price
                else:
                    hourly_volume = None

                # Calculate 24h price change if not provided
                price_change_24h = price_record.get('price_change_24h')
                price_change_percentage_24h = price_record.get('price_change_percentage_24h')
                
                # Note: percent_change_24h column contains correct percentage values
                # price_change_24h column may have incorrect absolute values
                # If price change not provided, calculate it
                if price_change_24h is None or price_change_percentage_24h is None:
                    calc_change, calc_change_pct = self.calculate_price_change_24h(
                        price_record['symbol'], current_price, timestamp_iso
                    )
                    if calc_change is not None:
                        price_change_24h = calc_change
                        price_change_percentage_24h = calc_change_pct
                        logger.debug(f"Calculated 24h price change for {price_record['symbol']}: {calc_change_pct:.2f}%")

                # Ensure market_cap is properly mapped from available data
                market_cap = price_record.get('market_cap') or price_record.get('market_cap_usd')

                record = {
                    'symbol': price_record['symbol'],
                    'price_date': timestamp_iso.date(),
                    'price_hour': timestamp_iso.hour,
                    'timestamp_iso': timestamp_iso,
                    'current_price': current_price,
                    'volume_24h': volume_24h,
                    'hourly_volume': hourly_volume,
                    'market_cap': market_cap,
                    'price_change_24h': price_change_24h,
                    'price_change_percentage_24h': price_change_percentage_24h,
                    # Add OHLC fields from price_data directly
                    'open_price': price_record.get('open'),
                    'high_price': price_record.get('high'), 
                    'low_price': price_record.get('low'),
                    'close_price': price_record.get('close'),
                    'ohlc_volume': price_record.get('volume'),
                    'ohlc_source': 'price_data'
                }
                
                # Get enhanced OHLC data from ohlc_data table (512K records available)
                ohlc_data = self.get_daily_ohlc_data(symbol, timestamp_iso)
                if ohlc_data:
                    # Override with better quality OHLC data if available
                    record.update({
                        'open_price': ohlc_data.get('open_price'),
                        'high_price': ohlc_data.get('high_price'), 
                        'low_price': ohlc_data.get('low_price'),
                        'close_price': ohlc_data.get('close_price'),
                        'ohlc_volume': ohlc_data.get('ohlc_volume'),
                        'ohlc_source': ohlc_data.get('ohlc_source', 'ohlc_data')
                    })
                    logger.debug(f"📊 Enhanced OHLC data retrieved for {symbol} {timestamp_iso.date()}")
                
                # Add social sentiment features if available
                social_key = (record['symbol'], record['price_date'], record['price_hour'])
                social_sent = social_sent_lookup.get(social_key)
                existing = existing_lookup.get((record['price_date'], record['price_hour']))
                # Always update social sentiment fields if new data is available and differs from existing
                update_social = False
                if social_sent:
                    # Ensure post count and unique authors are always int, not None
                    post_count = social_sent.get('social_post_count')
                    if post_count is None:
                        post_count = 0
                    author_count = social_sent.get('social_unique_authors')
                    if author_count is None:
                        author_count = 0
                    # Always update if new value is different from existing (including zero)
                    for field, new_val in [
                        ('social_post_count', post_count),
                        ('social_avg_sentiment', social_sent.get('social_avg_sentiment')),
                        ('social_avg_confidence', social_sent.get('social_avg_confidence')),
                        ('social_unique_authors', author_count)
                    ]:
                        old_val = existing[field] if existing else None
                        if old_val is None or new_val != old_val:
                            update_social = True
                    record['social_post_count'] = post_count
                    record['social_avg_sentiment'] = social_sent.get('social_avg_sentiment')
                    record['social_avg_confidence'] = social_sent.get('social_avg_confidence')
                    record['social_unique_authors'] = author_count
                else:
                    # Set sensible defaults for social data when unavailable
                    record['social_post_count'] = 0
                    record['social_avg_sentiment'] = None
                    record['social_avg_confidence'] = None  
                    record['social_unique_authors'] = 0
                    record['social_weighted_sentiment'] = None
                    record['social_engagement_weighted_sentiment'] = None
                    record['social_verified_user_sentiment'] = None
                    record['social_total_engagement'] = 0
                if getattr(self, 'insert_only', False):
                    if not existing:
                        action = self.insert_or_update_record(record, conn=conn, cursor=update_cursor)
                        if action == "INSERTED":
                            processed_count += 1
                            self.processing_stats['total_processed'] += 1
                    else:
                        logger.info(f"Skipping update for {symbol} {timestamp_iso} (insert-only mode)")
                    continue
                need_update = update_social
                # Technical indicators (batch lookup with fallback calculation)
                import time as _time
                t0 = _time.time()
                tech_data = tech_lookup.get((timestamp_iso.date(), timestamp_iso.hour))
                calculated_tech = {}
                
                # If no technical data from batch lookup, calculate basic indicators
                if not tech_data or all(tech_data.get(f) is None for f in ['rsi_14', 'sma_20', 'sma_50', 'vwap']):
                    calculated_tech = self.calculate_missing_technical_indicators(symbol, timestamp_iso, current_price)
                    if tech_data:
                        tech_data.update(calculated_tech)
                    else:
                        tech_data = calculated_tech
                        
                fetch_type = "batch lookup"
                if calculated_tech:
                    fetch_type += " + calculation"
                    
                logger.info(f"⏱️ Technical indicators fetch: {(_time.time()-t0):.3f}s for {symbol} {timestamp_iso} ({fetch_type})")
                
                if (not existing or any((existing or {}).get(f) is None for f in ['rsi_14','sma_20','sma_50','ema_12','ema_26','macd_line','macd_signal','macd_histogram','bb_upper','bb_middle','bb_lower','stoch_k','stoch_d','atr_14','vwap'])) and tech_data:
                    record.update({k: v for k, v in tech_data.items() if v is not None and k in ['rsi_14','sma_20','sma_50','ema_12','ema_26','macd_line','macd_signal','macd_histogram','bb_upper','bb_middle','bb_lower','stoch_k','stoch_d','atr_14','vwap']})
                    need_update = True
                    
                t1 = _time.time()
                # Macro indicators (batch lookup with interpolation)
                try:
                    macro_data = macro_lookup.get((timestamp_iso.date(), timestamp_iso.hour))
                    
                    # If no macro data from lookup, get latest available
                    if not macro_data or all(macro_data.get(f) is None for f in ['vix', 'spx', 'dxy']):
                        latest_macro = self.get_latest_macro_data(timestamp_iso.date())
                        if latest_macro:
                            macro_data = latest_macro if not macro_data else {**macro_data, **latest_macro}
                    latest_macro = {}
                    
                    # If no macro data from batch lookup, get latest available data
                    if not macro_data or all(macro_data.get(f) is None for f in ['vix', 'spx', 'dxy', 'tnx']):
                        latest_macro = self.get_latest_macro_data(timestamp_iso.date())
                        if macro_data:
                            macro_data.update(latest_macro)
                        else:
                            macro_data = latest_macro
                            
                    fetch_type = "batch lookup"
                    if latest_macro:
                        fetch_type += " + interpolation"
                        
                    logger.info(f"⏱️ Macro indicators fetch: {(_time.time()-t1):.3f}s for {symbol} {timestamp_iso} ({fetch_type})")
                    if (not existing or any((existing or {}).get(f) is None for f in ['vix','spx','dxy','tnx','fed_funds_rate'])) and macro_data:
                        # Safely update only available macro indicators
                        for k in ['vix','spx','dxy','tnx','fed_funds_rate']:
                            if k in macro_data and macro_data[k] is not None:
                                record[k] = macro_data[k]
                        need_update = True
                except Exception as e:
                    logger.error(f"Error processing macro data for {symbol}: {e}")
                    # Continue processing without macro data
                t2 = _time.time()
                # Coin-specific crypto sentiment (batch lookup)
                coin_sentiment = coin_sent_lookup.get((symbol, timestamp_iso.date(), timestamp_iso.hour))
                logger.info(f"⏱️ Coin-specific crypto sentiment fetch: {(_time.time()-t2):.3f}s for {symbol} {timestamp_iso} (batch lookup)")
                if (not existing or any((existing or {}).get(f) is None for f in ['crypto_sentiment_count','avg_cryptobert_score','avg_vader_score','avg_textblob_score','avg_crypto_keywords_score'])) and coin_sentiment:
                    record['crypto_sentiment_count'] = coin_sentiment.get('sentiment_count', 0)
                    record['avg_cryptobert_score'] = coin_sentiment.get('avg_cryptobert_score')
                    record['avg_vader_score'] = coin_sentiment.get('avg_vader_score')
                    record['avg_textblob_score'] = coin_sentiment.get('avg_textblob_score')
                    record['avg_crypto_keywords_score'] = coin_sentiment.get('avg_crypto_keywords_score')
                    need_update = True
                # General crypto sentiment (batch lookup)
                general_sentiment = general_sent_lookup.get((timestamp_iso.date(), timestamp_iso.hour))
                logger.info(f"⏱️ General crypto sentiment fetch: {(_time.time()-t2):.3f}s for {symbol} {timestamp_iso} (batch lookup)")
                if (not existing or any((existing or {}).get(f) is None for f in ['general_crypto_sentiment_count','avg_general_cryptobert_score','avg_general_vader_score','avg_general_textblob_score','avg_general_crypto_keywords_score'])) and general_sentiment:
                    record['general_crypto_sentiment_count'] = general_sentiment.get('sentiment_count', 0)
                    record['avg_general_cryptobert_score'] = general_sentiment.get('avg_cryptobert_score')
                    record['avg_general_vader_score'] = general_sentiment.get('avg_vader_score')
                    record['avg_general_textblob_score'] = general_sentiment.get('avg_textblob_score')
                    record['avg_general_crypto_keywords_score'] = general_sentiment.get('avg_crypto_keywords_score')
                    need_update = True

                # Ensure all sentiment fields are present, even if missing from lookups
                sentiment_defaults = {
                    'crypto_sentiment_count': 0,
                    'avg_cryptobert_score': None,
                    'avg_vader_score': None,
                    'avg_textblob_score': None,
                    'avg_crypto_keywords_score': None,
                    'general_crypto_sentiment_count': 0,
                    'avg_general_cryptobert_score': None,
                    'avg_general_vader_score': None,
                    'avg_general_textblob_score': None,
                    'avg_general_crypto_keywords_score': None,
                    'stock_sentiment_count': 0,
                    'avg_finbert_sentiment_score': None,
                    'avg_fear_greed_score': None,
                    'avg_volatility_sentiment': None,
                    'avg_risk_appetite': None,
                    'avg_crypto_correlation': None
                }
                for field, default in sentiment_defaults.items():
                    if field not in record:
                        record[field] = default
                        logger.debug(f"Sentiment field {field} missing for {symbol} {timestamp_iso}, set to default {default}")
                t3 = _time.time()
                # Stock sentiment (batch lookup)
                stock_sentiment = stock_sent_lookup.get((timestamp_iso.date(), timestamp_iso.hour))
                logger.info(f"⏱️ Stock sentiment fetch: {(_time.time()-t3):.3f}s for {symbol} {timestamp_iso} (batch lookup)")
                if (not existing or any((existing or {}).get(f) is None for f in ['stock_sentiment_count','avg_finbert_sentiment_score','avg_fear_greed_score','avg_volatility_sentiment','avg_risk_appetite','avg_crypto_correlation'])) and stock_sentiment:
                    record['stock_sentiment_count'] = stock_sentiment.get('sentiment_count', 0)
                    record['avg_finbert_sentiment_score'] = stock_sentiment.get('avg_finbert_sentiment_score')
                    record['avg_fear_greed_score'] = stock_sentiment.get('avg_fear_greed_score')
                    record['avg_volatility_sentiment'] = stock_sentiment.get('avg_volatility_sentiment')
                    record['avg_risk_appetite'] = stock_sentiment.get('avg_risk_appetite')
                    record['avg_crypto_correlation'] = stock_sentiment.get('avg_crypto_correlation')
                    need_update = True
                
                # Advanced Sentiment Processing (NEW - uses 113,853 sentiment signals)
                t4 = _time.time()
                advanced_sentiment = self.get_advanced_sentiment_data(symbol, timestamp_iso.date())
                logger.info(f"⏱️ Advanced sentiment fetch: {(_time.time()-t4):.3f}s for {symbol} {timestamp_iso}")
                
                # Map advanced sentiment data to record
                sentiment_fields = ['social_sentiment_score', 'social_confidence', 'sentiment_strength', 
                                  'news_sentiment', 'news_volume', 'social_avg_sentiment', 'social_post_count',
                                  'weighted_sentiment', 'sentiment_momentum', 'sentiment_volatility',
                                  'data_quality_score', 'source_diversity', 'realtime_sentiment',
                                  'realtime_confidence', 'realtime_strength', 'realtime_signals']
                
                if advanced_sentiment:
                    for field in sentiment_fields:
                        if field in advanced_sentiment and (not existing or existing.get(field) is None):
                            record[field] = advanced_sentiment[field]
                            need_update = True
                    
                    logger.info(f"📊 {symbol}: Applied {len([f for f in sentiment_fields if f in advanced_sentiment])} advanced sentiment fields")
                
                # Only insert/update if missing fields were filled or record doesn't exist
                if not existing or need_update:
                    action = self.insert_or_update_record(record, conn=conn, cursor=update_cursor)
                    if action in ["INSERTED", "UPDATED"]:
                        processed_count += 1
                        self.processing_stats['total_processed'] += 1
                else:
                    logger.info(f"No missing fields to update for {symbol} {timestamp_iso}")
            except Exception as e:
                logger.error(f"Error processing record for {symbol}: {e}")
        update_cursor.close()
        conn.close()
        logger.info(f"Finished processing for symbol: {symbol}. Processed {processed_count} records.")
        return processed_count
    def run_update_cycle(self):
        """Run one complete update cycle for all symbols"""
        start_time = datetime.now()
        total_processed = 0
        logger.info("Starting materialized table update cycle...")
        for symbol in self.symbols:
            try:
                logger.info(f"Beginning update for symbol: {symbol}")
                # You must implement process_symbol_updates or copy it from the original script
                if hasattr(self, 'process_symbol_updates'):
                    processed = self.process_symbol_updates(symbol)
                else:
                    logger.warning("process_symbol_updates not implemented!")
                    processed = 0
                total_processed += processed
                logger.info(f"Finished update for symbol: {symbol}. {processed} records processed.")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.processing_stats['last_run'] = end_time
        self.processing_stats['processing_time'] = processing_time
        if total_processed > 0:
            logger.info(f"Update cycle complete: {total_processed} records processed in {processing_time:.1f}s")
        else:
            logger.info(f"Update cycle complete: No new data to process")
        return total_processed
    """Service to continuously update ml_features_materialized table with new data"""
    
    def __init__(self):
        self.db_config = {
            'host': 'host.docker.internal',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices',
            'autocommit': True
        }
        self.symbols = self.load_symbols_from_db()
        self.running = True
        self.last_processed_timestamps = {}
        self.processing_stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'total_updated': 0,
            'last_run': None,
            'processing_time': 0
        }

    def load_symbols_from_db(self):
        """Load all active coin symbols from the crypto_assets table."""
        symbols = []
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT symbol FROM crypto_assets WHERE is_active=1")
            symbols = [row['symbol'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            logger.info(f"✅ Loaded {len(symbols)} symbols from crypto_assets table.")
        except Exception as e:
            logger.error(f"❌ Error loading symbols from crypto_assets: {e}")
        return symbols

    # ...existing methods remain unchanged...

# --- FastAPI integration ---

app = FastAPI()
updater = RealTimeMaterializedTableUpdater()
run_lock = threading.Lock()
run_thread = None
last_run_error = None

def run_update_background():
    global last_run_error
    try:
        with run_lock:
            updater.run_update_cycle()
        last_run_error = None
    except Exception as e:
        import traceback
        last_run_error = traceback.format_exc()
        logger.error(f"Exception in background update: {last_run_error}")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """
    Prometheus metrics endpoint
    """
    stats = updater.processing_stats.copy()
    
    # Return Prometheus text format
    metrics_text = f"""# HELP materialized_updater_total_processed Total number of records processed
# TYPE materialized_updater_total_processed counter
materialized_updater_total_processed {stats.get('total_processed', 0)}

# HELP materialized_updater_total_inserted Total number of records inserted
# TYPE materialized_updater_total_inserted counter
materialized_updater_total_inserted {stats.get('total_inserted', 0)}

# HELP materialized_updater_total_updated Total number of records updated
# TYPE materialized_updater_total_updated counter
materialized_updater_total_updated {stats.get('total_updated', 0)}

# HELP materialized_updater_active_connections Number of active database connections
# TYPE materialized_updater_active_connections gauge
materialized_updater_active_connections 1

# HELP materialized_updater_last_update_timestamp Last update timestamp
# TYPE materialized_updater_last_update_timestamp gauge
materialized_updater_last_update_timestamp {int(time.time())}

# HELP materialized_updater_running Service running status
# TYPE materialized_updater_running gauge
materialized_updater_running {1 if updater.running else 0}
"""
    return PlainTextResponse(metrics_text, media_type="text/plain")

@app.get("/status")
def status():
    # Return a summary of the last run and current state
    stats = updater.processing_stats.copy()
    stats["running"] = updater.running
    stats["symbols"] = updater.symbols
    if last_run_error:
        stats["last_run_error"] = last_run_error
    return stats

@app.post("/run")
def run(background_tasks: BackgroundTasks):
    global run_thread
    if run_lock.locked():
        return JSONResponse(status_code=409, content={"status": "busy", "message": "Update already running"})
    background_tasks.add_task(run_update_background)
    return {"status": "started"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Real-time Materialized Table Updater')
    parser.add_argument('--interval', type=int, default=5,
                       help='Update interval in minutes (default: 5)')
    parser.add_argument('--symbols', nargs='+',
                       help='Specific symbols to monitor (default: all)')
    parser.add_argument('--only-social-sentiment-symbols', action='store_true',
                       help='Only process symbols present in both social_sentiment_data and crypto_assets')
    parser.add_argument('--status', action='store_true',
                       help='Show current status and exit')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD) for processing (default: 7 days ago)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD) for processing (default: today)')
    parser.add_argument('--update-if-changed', action='store_true',
                       help='Update records if new data fills missing fields (default behavior)')
    parser.add_argument('--insert-only', action='store_true',
                       help='Only insert new records if they do not already exist; skip all updates')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously with specified interval (for deployment mode)')
    args = parser.parse_args()
    # CLI mode for manual runs
    if args.only_social_sentiment_symbols:
        updater.symbols = updater.get_symbols_with_social_sentiment()
        logger.info(f"🎯 Monitoring only symbols with social sentiment: {updater.symbols}")
    elif args.symbols:
        updater.symbols = args.symbols
        logger.info(f"🎯 Monitoring specific symbols: {args.symbols}")
    today = datetime.now().date()
    default_start = today - timedelta(days=7)
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else default_start
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else today
    updater.start_date = start_date
    updater.end_date = end_date
    updater.update_if_changed = args.update_if_changed or not args.insert_only
    updater.insert_only = args.insert_only
    if args.status:
        updater.display_status()
    elif args.continuous:
        # Continuous mode for deployment
        import time
        logger.info(f"🔄 Starting continuous mode with {args.interval} minute intervals")
        while True:
            try:
                logger.info("▶️ Starting update cycle...")
                updater.run_update_cycle()
                logger.info(f"✅ Update cycle complete. Sleeping for {args.interval} minutes...")
                time.sleep(args.interval * 60)  # Convert minutes to seconds
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous mode: {e}")
                logger.info(f"⏳ Waiting {args.interval} minutes before retry...")
                time.sleep(args.interval * 60)
    else:
        # Single run mode
        updater.run_update_cycle()
