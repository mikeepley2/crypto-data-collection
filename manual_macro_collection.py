#!/usr/bin/env python3
"""
Manual Macro Data Collection - Update stale indicators
"""
import requests
import mysql.connector
from datetime import datetime, timedelta
import time
import os

# Database configuration
db_config = {
    'host': '192.168.230.162',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

# FRED API configuration
FRED_API_KEY = '1e8b4e2b6b7e8f9b5c9d8f7e6d5c4b3a'  # From historical collector
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

def collect_recent_macro_data():
    """Collect recent macro data for stale indicators"""
    print("=== MANUAL MACRO DATA COLLECTION ===")
    
    # Key indicators to update
    fred_series = {
        'FEDFUNDS': 'Fed_Funds_Rate',
        'DGS10': 'Treasury_10Y',
        'DGS2': 'Treasury_2Y', 
        'UNRATE': 'Unemployment_Rate',
        'CPIAUCSL': 'CPI',
        'VIXCLS': 'VIX',
        'DEXUSEU': 'DXY',
        'DEXJPUS': 'JPY_USD'
    }
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    total_inserted = 0
    
    try:
        for series_id, indicator_name in fred_series.items():
            print(f"Collecting {indicator_name} ({series_id})...")
            
            try:
                # Get recent data (last 30 days)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                response = requests.get(
                    f"{FRED_BASE_URL}/series/observations",
                    params={
                        'series_id': series_id,
                        'api_key': FRED_API_KEY,
                        'file_type': 'json',
                        'observation_start': start_date,
                        'observation_end': end_date,
                        'sort_order': 'desc',
                        'limit': 10  # Just get recent values
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'observations' in data:
                        records_inserted = 0
                        for obs in data['observations']:
                            if obs['value'] != '.':  # FRED uses '.' for missing
                                try:
                                    value = float(obs['value'])
                                    obs_date = datetime.strptime(obs['date'], '%Y-%m-%d').date()
                                    
                                    cursor.execute("""
                                        INSERT IGNORE INTO macro_indicators (
                                            indicator_name, indicator_date, value,
                                            data_source, frequency, collected_at
                                        ) VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (
                                        indicator_name, obs_date, value,
                                        'fred_manual', 'daily', datetime.now()
                                    ))
                                    
                                    if cursor.rowcount > 0:
                                        records_inserted += 1
                                        
                                except (ValueError, TypeError) as e:
                                    print(f"   Invalid value: {obs['value']}")
                        
                        conn.commit()
                        total_inserted += records_inserted
                        print(f"   Inserted {records_inserted} new records")
                    else:
                        print(f"   No observations found")
                else:
                    print(f"   FRED API error: {response.status_code}")
                    
            except Exception as e:
                print(f"   Error collecting {series_id}: {e}")
            
            # Rate limiting
            time.sleep(1)
                
    finally:
        cursor.close()
        conn.close()
    
    print(f"\nTotal new records inserted: {total_inserted}")
    return total_inserted

def collect_yahoo_finance_data():
    """Collect current market data from Yahoo Finance"""
    print("\n=== YAHOO FINANCE DATA COLLECTION ===")
    
    # Market indicators
    symbols = {
        '^VIX': 'VIX',
        '^GSPC': 'SPX',
        'DX-Y.NYB': 'DXY',
        '^TNX': 'TNX',
        'GC=F': 'GOLD',
        'CL=F': 'OIL'
    }
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    total_inserted = 0
    
    try:
        import yfinance as yf
        
        for symbol, indicator_name in symbols.items():
            print(f"Collecting {indicator_name} ({symbol})...")
            
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                
                if not hist.empty:
                    latest_close = hist['Close'].iloc[-1]
                    latest_date = hist.index[-1].date()
                    
                    cursor.execute("""
                        INSERT INTO macro_indicators (
                            indicator_name, indicator_date, value,
                            data_source, frequency, collected_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            value = VALUES(value),
                            collected_at = VALUES(collected_at)
                    """, (
                        indicator_name, latest_date, float(latest_close),
                        'yahoo_finance_manual', 'daily', datetime.now()
                    ))
                    
                    total_inserted += 1
                    print(f"   Updated: {latest_close:.2f} for {latest_date}")
                else:
                    print(f"   No data found")
                    
            except Exception as e:
                print(f"   Error collecting {symbol}: {e}")
        
        conn.commit()
        
    except ImportError:
        print("yfinance not available - skipping Yahoo Finance collection")
    finally:
        cursor.close()
        conn.close()
    
    print(f"Total Yahoo Finance records: {total_inserted}")
    return total_inserted

if __name__ == "__main__":
    print("MANUAL MACRO DATA COLLECTION")
    print("=" * 40)
    
    fred_records = collect_recent_macro_data()
    yahoo_records = collect_yahoo_finance_data()
    
    total_records = fred_records + yahoo_records
    
    print(f"\n" + "=" * 40)
    print(f"COLLECTION COMPLETE")
    print(f"Total new/updated records: {total_records}")
    print(f"=" * 40)