#!/bin/bash
# Enhanced Daily Macro Collection Script  
# This script ensures daily collection of macro indicators
# Schedule with cron: 0 9 * * * /e/git/crypto-data-collection/daily_macro_collection.sh

set -e  # Exit on any error

SCRIPT_DIR="/mnt/e/git/crypto-data-collection"
LOG_FILE="$SCRIPT_DIR/macro_collection.log"
VENV_PATH="$SCRIPT_DIR/venv"

# Create log directory if it doesn't exist - use local log
LOG_FILE="$SCRIPT_DIR/macro_collection.log"
touch $LOG_FILE

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

log_message "=== Daily Macro Collection Starting ==="

# Change to project directory
cd $SCRIPT_DIR

# Activate virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source $VENV_PATH/bin/activate
    log_message "Virtual environment activated"
else
    log_message "WARNING: Virtual environment not found at $VENV_PATH"
fi

# Run daily macro collection
python3 -c "
import mysql.connector
import requests
import json
from datetime import datetime, timedelta
import logging

# Configure logging to both file and stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('macro_collection_detailed.log'),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    return mysql.connector.connect(
        host='172.22.32.1',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )

def fetch_fred_data(series_id, days_back=7):
    '''Fetch recent data from FRED API'''
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    url = 'https://api.stlouisfed.org/fred/series/observations'
    params = {
        'series_id': series_id,
        'file_type': 'json',
        'observation_start': start_date,
        'observation_end': end_date,
        'api_key': '35478996c5e061d0fc99fc73f5ce348d'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        observations = []
        if 'observations' in data:
            for obs in data['observations']:
                if obs['value'] != '.':
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
        
        return observations
    except Exception as e:
        logging.error(f'Failed to fetch {series_id}: {e}')
        return []

def insert_macro_data(indicator_name, observations, data_source='daily_collection'):
    '''Insert data into macro_indicators table'''
    if not observations:
        return 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted = 0
    
    try:
        for obs in observations:
            # Check if already exists
            cursor.execute('''
                SELECT COUNT(*) FROM macro_indicators
                WHERE indicator_name = %s AND indicator_date = %s
            ''', (indicator_name, obs['date']))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO macro_indicators 
                    (indicator_name, indicator_date, value, data_source, collected_at)
                    VALUES (%s, %s, %s, %s, NOW())
                ''', (indicator_name, obs['date'], obs['value'], data_source))
                inserted += 1
        
        conn.commit()
        
    except Exception as e:
        logging.error(f'Error inserting {indicator_name}: {e}')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return inserted

# Daily indicators that need regular updates
daily_indicators = {
    'DGS10': 'DGS10',       # 10-Year Treasury (Daily)
    'DGS2': 'DGS2',         # 2-Year Treasury (Daily)  
    'DEXJPUS': 'DEXJPUS',   # USD/JPY Exchange Rate (Daily)
    'DEXUSEU': 'DEXUSEU',   # USD/EUR Exchange Rate (Daily)
    'VIX': 'VIXCLS'         # VIX Volatility Index (Daily)
}

# Monthly indicators (check weekly)
monthly_indicators = {
    'UNRATE': 'UNRATE',     # Unemployment Rate (Monthly)
    'CPIAUCSL': 'CPIAUCSL', # Consumer Price Index (Monthly)
    'FEDFUNDS': 'FEDFUNDS'  # Federal Funds Rate (Monthly)
}

# Quarterly indicators (check monthly)
quarterly_indicators = {
    'GDP': 'GDPC1'          # Real GDP (Quarterly)
}

total_updated = 0

logging.info('=== Daily Macro Collection Started ===')

# Process daily indicators (look back 7 days)
for indicator, fred_code in daily_indicators.items():
    logging.info(f'Processing daily indicator: {indicator}')
    observations = fetch_fred_data(fred_code, days_back=7)
    updated = insert_macro_data(indicator, observations)
    total_updated += updated
    logging.info(f'{indicator}: {updated} new records')

# Process monthly indicators (look back 35 days)
for indicator, fred_code in monthly_indicators.items():
    logging.info(f'Processing monthly indicator: {indicator}')
    observations = fetch_fred_data(fred_code, days_back=35)
    updated = insert_macro_data(indicator, observations)
    total_updated += updated
    logging.info(f'{indicator}: {updated} new records')

# Process quarterly indicators (look back 95 days)
for indicator, fred_code in quarterly_indicators.items():
    logging.info(f'Processing quarterly indicator: {indicator}')
    observations = fetch_fred_data(fred_code, days_back=95)
    updated = insert_macro_data(indicator, observations)
    total_updated += updated
    logging.info(f'{indicator}: {updated} new records')

logging.info(f'=== Daily Collection Complete: {total_updated} total records updated ===')
print(f'Daily macro collection completed: {total_updated} records updated')
"

# Log completion status
COLLECTION_RESULT=$?
if [ $COLLECTION_RESULT -eq 0 ]; then
    log_message "Daily macro collection completed successfully"
else
    log_message "ERROR: Daily macro collection failed with exit code $COLLECTION_RESULT"
fi

log_message "=== Daily Macro Collection Finished ==="