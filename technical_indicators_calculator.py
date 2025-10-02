#!/usr/bin/env python3
"""
TECHNICAL INDICATORS CALCULATOR
A comprehensive technical indicators calculator to replace the buggy service
Calculates RSI, MACD, SMA, EMA, Bollinger Bands, and more from price data
"""

import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicatorsCalculator:
    """Calculate comprehensive technical indicators from OHLC price data"""
    
    def __init__(self):
        self.db_config = {
            'host': '192.168.230.162',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
    
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def get_price_data(self, symbol: str, days_back: int = 200) -> pd.DataFrame:
        """Get OHLC price data for technical indicators calculation"""
        conn = self.get_db_connection()
        
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM hourly_data 
            WHERE symbol = %s 
            AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY timestamp ASC
        """
        
        df = pd.read_sql(query, conn, params=(symbol, days_back))
        conn.close()
        
        if df.empty:
            return df
            
        # Ensure we have the required columns and proper data types
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Convert to float for calculations
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period, min_periods=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        macd_signal = self.calculate_ema(macd_line, signal)
        macd_histogram = macd_line - macd_signal
        
        return {
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        bb_upper = sma + (std * std_dev)
        bb_lower = sma - (std * std_dev)
        bb_width = (bb_upper - bb_lower) / sma * 100
        
        return {
            'bb_upper': bb_upper,
            'bb_middle': sma,
            'bb_lower': bb_lower,
            'bb_width': bb_width
        }
    
    def calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """Calculate Stochastic Oscillator"""
        lowest_low = df['low'].rolling(window=period).min()
        highest_high = df['high'].rolling(window=period).max()
        
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=3).mean()
        
        return {
            'stoch_k': k_percent,
            'stoch_d': d_percent
        }
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        return williams_r
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close_prev = np.abs(df['high'] - df['close'].shift())
        low_close_prev = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close_prev, low_close_prev))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap
    
    def calculate_all_indicators(self, symbol: str, days_back: int = 200) -> Optional[pd.DataFrame]:
        """Calculate all technical indicators for a symbol"""
        logger.info(f"📊 Calculating technical indicators for {symbol}...")
        
        # Get price data
        df = self.get_price_data(symbol, days_back)
        if df.empty:
            logger.warning(f"⚠️ No price data found for {symbol}")
            return None
        
        logger.info(f"   Retrieved {len(df)} price records")
        
        # Initialize indicators dataframe
        indicators = pd.DataFrame(index=df.index)
        indicators['symbol'] = symbol
        
        # Simple Moving Averages
        indicators['sma_20'] = self.calculate_sma(df['close'], 20)
        indicators['sma_50'] = self.calculate_sma(df['close'], 50)
        indicators['sma_200'] = self.calculate_sma(df['close'], 200)
        
        # Exponential Moving Averages
        indicators['ema_12'] = self.calculate_ema(df['close'], 12)
        indicators['ema_26'] = self.calculate_ema(df['close'], 26)
        indicators['ema_50'] = self.calculate_ema(df['close'], 50)
        
        # RSI
        indicators['rsi_14'] = self.calculate_rsi(df['close'], 14)
        
        # MACD
        macd_data = self.calculate_macd(df['close'])
        indicators['macd_line'] = macd_data['macd_line']
        indicators['macd_signal'] = macd_data['macd_signal']
        indicators['macd_histogram'] = macd_data['macd_histogram']
        
        # Bollinger Bands
        bb_data = self.calculate_bollinger_bands(df['close'])
        indicators['bb_upper'] = bb_data['bb_upper']
        indicators['bb_middle'] = bb_data['bb_middle']
        indicators['bb_lower'] = bb_data['bb_lower']
        indicators['bb_width'] = bb_data['bb_width']
        
        # Stochastic
        stoch_data = self.calculate_stochastic(df)
        indicators['stoch_k'] = stoch_data['stoch_k']
        indicators['stoch_d'] = stoch_data['stoch_d']
        
        # Williams %R
        indicators['williams_r'] = self.calculate_williams_r(df)
        
        # ATR (Average True Range)
        indicators['atr_14'] = self.calculate_atr(df)
        
        # VWAP
        indicators['vwap'] = self.calculate_vwap(df)
        
        # Additional indicators
        indicators['momentum'] = df['close'].pct_change(periods=10) * 100
        indicators['roc'] = df['close'].pct_change(periods=12) * 100  # Rate of Change
        
        # Volume indicators
        indicators['volume_sma'] = self.calculate_sma(df['volume'], 20)
        indicators['obv'] = (df['volume'] * np.where(df['close'] > df['close'].shift(), 1, -1)).cumsum()
        
        # Volatility
        indicators['volatility'] = df['close'].pct_change().rolling(window=30).std() * 100
        
        # Remove rows with insufficient data (first 200 rows typically)
        indicators = indicators.dropna(subset=['sma_200'])
        
        logger.info(f"   ✅ Calculated indicators for {len(indicators)} periods")
        return indicators
    
    def store_indicators(self, indicators_df: pd.DataFrame, symbol: str) -> int:
        """Store calculated indicators in the database"""
        if indicators_df is None or indicators_df.empty:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Prepare insert query
        insert_query = """
            INSERT INTO technical_indicators (
                symbol, timestamp_iso, updated_at,
                sma_20, sma_50, sma_200, ema_12, ema_26, ema_50,
                rsi_14, macd_line, macd_signal, macd_histogram,
                bb_upper, bb_middle, bb_lower, bb_width,
                stoch_k, stoch_d, williams_r, atr_14, vwap,
                momentum, roc, volume_sma, obv, volatility
            ) VALUES (
                %s, %s, NOW(),
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                updated_at = NOW(),
                sma_20 = VALUES(sma_20),
                sma_50 = VALUES(sma_50),
                sma_200 = VALUES(sma_200),
                ema_12 = VALUES(ema_12),
                ema_26 = VALUES(ema_26),
                ema_50 = VALUES(ema_50),
                rsi_14 = VALUES(rsi_14),
                macd_line = VALUES(macd_line),
                macd_signal = VALUES(macd_signal),
                macd_histogram = VALUES(macd_histogram),
                bb_upper = VALUES(bb_upper),
                bb_middle = VALUES(bb_middle),
                bb_lower = VALUES(bb_lower),
                bb_width = VALUES(bb_width),
                stoch_k = VALUES(stoch_k),
                stoch_d = VALUES(stoch_d),
                williams_r = VALUES(williams_r),
                atr_14 = VALUES(atr_14),
                vwap = VALUES(vwap),
                momentum = VALUES(momentum),
                roc = VALUES(roc),
                volume_sma = VALUES(volume_sma),
                obv = VALUES(obv),
                volatility = VALUES(volatility)
        """
        
        records_inserted = 0
        
        for timestamp, row in indicators_df.iterrows():
            try:
                values = (
                    symbol, timestamp,
                    float(row['sma_20']) if pd.notna(row['sma_20']) else None,
                    float(row['sma_50']) if pd.notna(row['sma_50']) else None,
                    float(row['sma_200']) if pd.notna(row['sma_200']) else None,
                    float(row['ema_12']) if pd.notna(row['ema_12']) else None,
                    float(row['ema_26']) if pd.notna(row['ema_26']) else None,
                    float(row['ema_50']) if pd.notna(row['ema_50']) else None,
                    float(row['rsi_14']) if pd.notna(row['rsi_14']) else None,
                    float(row['macd_line']) if pd.notna(row['macd_line']) else None,
                    float(row['macd_signal']) if pd.notna(row['macd_signal']) else None,
                    float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None,
                    float(row['bb_upper']) if pd.notna(row['bb_upper']) else None,
                    float(row['bb_middle']) if pd.notna(row['bb_middle']) else None,
                    float(row['bb_lower']) if pd.notna(row['bb_lower']) else None,
                    float(row['bb_width']) if pd.notna(row['bb_width']) else None,
                    float(row['stoch_k']) if pd.notna(row['stoch_k']) else None,
                    float(row['stoch_d']) if pd.notna(row['stoch_d']) else None,
                    float(row['williams_r']) if pd.notna(row['williams_r']) else None,
                    float(row['atr_14']) if pd.notna(row['atr_14']) else None,
                    float(row['vwap']) if pd.notna(row['vwap']) else None,
                    float(row['momentum']) if pd.notna(row['momentum']) else None,
                    float(row['roc']) if pd.notna(row['roc']) else None,
                    float(row['volume_sma']) if pd.notna(row['volume_sma']) else None,
                    float(row['obv']) if pd.notna(row['obv']) else None,
                    float(row['volatility']) if pd.notna(row['volatility']) else None
                )
                
                cursor.execute(insert_query, values)
                records_inserted += 1
                
            except Exception as e:
                logger.error(f"Error inserting record for {symbol} at {timestamp}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"   💾 Stored {records_inserted} indicator records for {symbol}")
        return records_inserted
    
    def generate_indicators_for_symbol(self, symbol: str, days_back: int = 200) -> int:
        """Generate technical indicators for a single symbol"""
        try:
            # Calculate indicators
            indicators_df = self.calculate_all_indicators(symbol, days_back)
            if indicators_df is None:
                return 0
            
            # Store in database
            records_stored = self.store_indicators(indicators_df, symbol)
            return records_stored
            
        except Exception as e:
            logger.error(f"❌ Error generating indicators for {symbol}: {e}")
            return 0
    
    def generate_indicators_for_major_symbols(self) -> Dict[str, int]:
        """Generate technical indicators for all major crypto symbols"""
        logger.info("🚀 Starting technical indicators generation for major symbols...")
        
        # Major crypto symbols
        major_symbols = [
            'BTC', 'ETH', 'SOL', 'ADA', 'MATIC', 'AVAX', 'DOT', 'LINK', 
            'UNI', 'ATOM', 'AAVE', 'ALGO', 'XLM', 'ICP', 'FTM'
        ]
        
        results = {}
        total_records = 0
        
        for symbol in major_symbols:
            logger.info(f"\n📊 Processing {symbol}...")
            
            try:
                records = self.generate_indicators_for_symbol(symbol, days_back=200)
                results[symbol] = records
                total_records += records
                
                logger.info(f"✅ {symbol}: {records} records generated")
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Failed to process {symbol}: {e}")
                results[symbol] = 0
        
        logger.info(f"\n🎯 GENERATION COMPLETE:")
        logger.info(f"   Total symbols processed: {len(major_symbols)}")
        logger.info(f"   Total records generated: {total_records:,}")
        logger.info(f"   Success rate: {len([r for r in results.values() if r > 0])}/{len(major_symbols)}")
        
        return results

def main():
    """Main function to run the technical indicators calculator"""
    calculator = TechnicalIndicatorsCalculator()
    
    print("=== TECHNICAL INDICATORS CALCULATOR ===\n")
    print("This will generate comprehensive technical indicators for major crypto symbols")
    print("Including: RSI, MACD, SMA, EMA, Bollinger Bands, Stochastic, Williams %R, ATR, VWAP\n")
    
    # Generate indicators for all major symbols
    results = calculator.generate_indicators_for_major_symbols()
    
    print(f"\n=== GENERATION RESULTS ===")
    for symbol, count in results.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {symbol}: {count:,} records")
    
    total_success = sum(1 for count in results.values() if count > 0)
    print(f"\nSummary: {total_success}/{len(results)} symbols successful")

if __name__ == "__main__":
    main()