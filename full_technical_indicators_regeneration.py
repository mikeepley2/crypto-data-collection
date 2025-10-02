#!/usr/bin/env python3
"""
FULL TECHNICAL INDICATORS REGENERATION
Regenerate complete technical indicators dataset from historical price data
No confirmation prompts - runs automatically
"""

import mysql.connector
import logging
import time
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullTechnicalIndicatorsRegenerator:
    """Regenerate complete technical indicators dataset from historical price data"""
    
    def __init__(self):
        self.db_config = {
            'host': '192.168.230.162',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
        
        # Processing configuration
        self.batch_size = 1000
        self.min_periods_required = 200  # Need 200 periods for SMA200
        
        logger.info("Full Technical Indicators Regenerator initialized")
    
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def get_all_symbols_for_processing(self) -> List[Tuple[str, int]]:
        """Get ALL symbols with sufficient data for processing"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get ALL symbols with enough historical data
        cursor.execute("""
            SELECT 
                symbol, 
                COUNT(*) as record_count
            FROM hourly_data 
            GROUP BY symbol
            HAVING COUNT(*) >= %s
            ORDER BY COUNT(*) DESC
        """, (self.min_periods_required,))
        
        symbols_data = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(symbols_data)} symbols with sufficient data")
        for symbol, count in symbols_data[:10]:  # Show top 10
            logger.info(f"  {symbol}: {count:,} historical records")
        
        return symbols_data
    
    def calculate_sma(self, prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average"""
        sma_values = []
        
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(None)
            else:
                period_prices = prices[i - period + 1:i + 1]
                sma = sum(period_prices) / len(period_prices)
                sma_values.append(sma)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average"""
        ema_values = []
        multiplier = 2.0 / (period + 1)
        
        for i in range(len(prices)):
            if i == 0:
                ema_values.append(prices[0])
            else:
                ema = (prices[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
                ema_values.append(ema)
        
        return ema_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate RSI using Wilder's smoothing method"""
        rsi_values = [None] * period
        
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        # Calculate price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Initial averages using SMA for first calculation
        gains = [max(0, change) for change in changes[:period]]
        losses = [abs(min(0, change)) for change in changes[:period]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        # Calculate RSI for each point after initial period
        for i in range(period, len(prices)):
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
            
            # Update averages using Wilder's method (EMA with alpha = 1/period)
            if i < len(changes):
                gain = max(0, changes[i])
                loss = abs(min(0, changes[i]))
                avg_gain = ((avg_gain * (period - 1)) + gain) / period
                avg_loss = ((avg_loss * (period - 1)) + loss) / period
        
        return rsi_values
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate MACD, Signal, and Histogram"""
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        # MACD line
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(None)
        
        # Signal line (EMA of MACD)
        macd_values_for_signal = [x for x in macd_line if x is not None]
        signal_line_values = self.calculate_ema(macd_values_for_signal, signal)
        
        # Align signal line with original data
        signal_line = [None] * len(prices)
        signal_idx = 0
        for i in range(len(macd_line)):
            if macd_line[i] is not None:
                if signal_idx < len(signal_line_values):
                    signal_line[i] = signal_line_values[signal_idx]
                signal_idx += 1
        
        # Histogram
        histogram = []
        for i in range(len(prices)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
        """Calculate Bollinger Bands"""
        sma = self.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1 or sma[i] is None:
                upper_band.append(None)
                lower_band.append(None)
            else:
                period_prices = prices[i - period + 1:i + 1]
                std = math.sqrt(sum((x - sma[i]) ** 2 for x in period_prices) / period)
                upper_band.append(sma[i] + (std_dev * std))
                lower_band.append(sma[i] - (std_dev * std))
        
        return sma, upper_band, lower_band
    
    def process_symbol_full(self, symbol: str) -> int:
        """Process a single symbol with ALL available historical data"""
        logger.info(f"Processing {symbol} - FULL DATASET...")
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get ALL price data for this symbol
            cursor.execute("""
                SELECT timestamp, close, high, low, volume
                FROM hourly_data 
                WHERE symbol = %s 
                AND close IS NOT NULL
                ORDER BY timestamp ASC
            """, (symbol,))
            
            price_data = cursor.fetchall()
            
            if len(price_data) < self.min_periods_required:
                logger.warning(f"Insufficient data for {symbol}: only {len(price_data)} records")
                return 0
            
            logger.info(f"Processing {len(price_data):,} historical records for {symbol}")
            
            # Extract data
            timestamps = [row[0] for row in price_data]
            closes = [float(row[1]) for row in price_data]
            highs = [float(row[2]) if row[2] is not None else float(row[1]) for row in price_data]
            lows = [float(row[3]) if row[3] is not None else float(row[1]) for row in price_data]
            volumes = [float(row[4]) if row[4] is not None else 0.0 for row in price_data]
            
            # Calculate ALL indicators
            logger.info(f"Calculating technical indicators for {symbol}...")
            
            # Moving Averages (using existing column names)
            sma_10 = self.calculate_sma(closes, 10)
            sma_20 = self.calculate_sma(closes, 20)
            sma_30 = self.calculate_sma(closes, 30)
            sma_50 = self.calculate_sma(closes, 50)
            sma_200 = self.calculate_sma(closes, 200)
            
            # EMAs (using existing column names)
            ema_12 = self.calculate_ema(closes, 12)
            ema_20 = self.calculate_ema(closes, 20)
            ema_26 = self.calculate_ema(closes, 26)
            ema_50 = self.calculate_ema(closes, 50)
            ema_200 = self.calculate_ema(closes, 200)
            
            # Momentum indicators
            rsi_14 = self.calculate_rsi(closes, 14)
            
            # MACD
            macd, macd_signal, macd_histogram = self.calculate_macd(closes)
            
            # Bollinger Bands
            bb_middle, bb_upper, bb_lower = self.calculate_bollinger_bands(closes)
            
            logger.info(f"Storing indicators to database for {symbol}...")
            
            # Store results in batches
            insert_query = """
                INSERT INTO technical_indicators (
                    symbol, timestamp_iso, updated_at,
                    sma_10, sma_20, sma_30, sma_50, sma_200,
                    ema_12, ema_20, ema_26, ema_50, ema_200,
                    rsi_14, macd, macd_signal, macd_histogram,
                    bb_upper, bb_middle, bb_lower
                ) VALUES (
                    %s, %s, NOW(), 
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    updated_at = NOW(),
                    sma_10 = VALUES(sma_10), sma_20 = VALUES(sma_20), sma_30 = VALUES(sma_30),
                    sma_50 = VALUES(sma_50), sma_200 = VALUES(sma_200),
                    ema_12 = VALUES(ema_12), ema_20 = VALUES(ema_20), ema_26 = VALUES(ema_26),
                    ema_50 = VALUES(ema_50), ema_200 = VALUES(ema_200),
                    rsi_14 = VALUES(rsi_14), macd = VALUES(macd), macd_signal = VALUES(macd_signal),
                    macd_histogram = VALUES(macd_histogram), bb_upper = VALUES(bb_upper),
                    bb_middle = VALUES(bb_middle), bb_lower = VALUES(bb_lower)
            """
            
            records_inserted = 0
            batch_data = []
            
            # Start from index where SMA200 becomes valid
            start_idx = 199
            
            for i in range(start_idx, len(price_data)):
                # Only insert if we have valid SMA200 (our most restrictive indicator)
                if sma_200[i] is not None:
                    
                    values = (
                        symbol, timestamps[i],
                        sma_10[i], sma_20[i], sma_30[i], sma_50[i], sma_200[i],
                        ema_12[i], ema_20[i], ema_26[i], ema_50[i], ema_200[i],
                        rsi_14[i], macd[i], macd_signal[i], macd_histogram[i],
                        bb_upper[i], bb_middle[i], bb_lower[i]
                    )
                    
                    batch_data.append(values)
                    
                    # Process in batches
                    if len(batch_data) >= self.batch_size:
                        cursor.executemany(insert_query, batch_data)
                        conn.commit()
                        records_inserted += len(batch_data)
                        logger.info(f"  {symbol}: Inserted {records_inserted:,} indicators...")
                        batch_data = []
            
            # Insert remaining batch
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                conn.commit()
                records_inserted += len(batch_data)
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ {symbol}: Generated {records_inserted:,} indicators from {len(price_data):,} price records")
            return records_inserted
            
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
            return 0

def main():
    """Main regeneration process"""
    print("=" * 70)
    print("FULL TECHNICAL INDICATORS REGENERATION - AUTO MODE")
    print("=" * 70)
    print("Regenerating ALL technical indicators from complete historical data")
    print("Using EXACT mathematical formulas - no estimates or mock data")
    print("Processing ALL available symbols and ALL available historical data")
    print()
    
    start_time = time.time()
    regenerator = FullTechnicalIndicatorsRegenerator()
    
    # Get ALL symbols to process
    symbols_data = regenerator.get_all_symbols_for_processing()
    print(f"Processing {len(symbols_data)} symbols with sufficient historical data...")
    print()
    
    total_generated = 0
    successful_symbols = 0
    
    for i, (symbol, record_count) in enumerate(symbols_data, 1):
        print(f"[{i}/{len(symbols_data)}] Processing {symbol} ({record_count:,} historical records)...")
        
        generated = regenerator.process_symbol_full(symbol)
        if generated > 0:
            total_generated += generated
            successful_symbols += 1
        
        print(f"Progress: {i}/{len(symbols_data)} symbols completed ({successful_symbols} successful)")
        print("-" * 50)
    
    elapsed_time = time.time() - start_time
    
    print("=" * 70)
    print("FULL REGENERATION COMPLETE")
    print("=" * 70)
    print(f"Total symbols processed: {len(symbols_data)}")
    print(f"Successful symbols: {successful_symbols}")
    print(f"Total indicators generated: {total_generated:,}")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    print()
    print("All indicators calculated from real historical price data using exact formulas")
    print("No estimates, no mock data - 100% authentic technical analysis")
    print("=" * 70)

if __name__ == "__main__":
    main()