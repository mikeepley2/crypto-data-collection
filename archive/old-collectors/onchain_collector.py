#!/usr/bin/env python3
"""
CoinGecko Onchain Data Collector
Collects onchain metrics using premium CoinGecko API
"""

import os
import time
import requests
import mysql.connector
from datetime import datetime, timedelta
import logging
import json
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'host.docker.internal'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'cryptoai'),
    'password': os.getenv('DB_PASSWORD', 'CryptoAI2024!'),
    'database': os.getenv('DB_NAME', 'cryptoaidb'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# API configuration - Using premium CoinGecko API
API_KEY = os.getenv('COINGECKO_API_KEY', '')
BASE_URL = 'https://pro-api.coingecko.com/api/v3'

# Headers for premium API
HEADERS = {
    'accept': 'application/json',
    'x-cg-demo-api-key': API_KEY  # Premium API uses demo header format
}

# Top cryptocurrencies to collect data for
CRYPTO_IDS = [
    'bitcoin', 'ethereum', 'binancecoin', 'ripple', 'cardano',
    'solana', 'dogecoin', 'polygon', 'avalanche-2', 'chainlink',
    'uniswap', 'litecoin', 'bitcoin-cash', 'ethereum-classic', 'stellar'
]

def get_db_connection():
    """Get database connection with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            logger.info("✅ Database connection established")
            return connection
        except mysql.connector.Error as e:
            logger.error(f"❌ Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

def create_table_if_not_exists(connection):
    """Create onchain data table if it doesn't exist"""
    cursor = connection.cursor()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS crypto_onchain_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        coin_id VARCHAR(50) NOT NULL,
        market_cap DECIMAL(20, 2),
        fully_diluted_valuation DECIMAL(20, 2),
        total_volume DECIMAL(20, 2),
        circulating_supply DECIMAL(20, 2),
        total_supply DECIMAL(20, 2),
        max_supply DECIMAL(20, 2),
        ath DECIMAL(20, 8),
        ath_date DATETIME,
        atl DECIMAL(20, 8),
        atl_date DATETIME,
        price_change_percentage_24h DECIMAL(10, 4),
        price_change_percentage_7d DECIMAL(10, 4),
        price_change_percentage_30d DECIMAL(10, 4),
        market_cap_rank INT,
        market_cap_change_percentage_24h DECIMAL(10, 4),
        volume_to_market_cap_ratio DECIMAL(10, 6),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_symbol_created (symbol, created_at),
        INDEX idx_coin_id_created (coin_id, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_sql)
    connection.commit()
    cursor.close()
    logger.info("✅ Table crypto_onchain_data ready")

def fetch_onchain_data():
    """Fetch onchain data from CoinGecko API"""
    try:
        # Use premium API endpoint for market data
        url = f"{BASE_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(CRYPTO_IDS),
            'order': 'market_cap_desc',
            'per_page': len(CRYPTO_IDS),
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h,7d,30d'
        }
        
        logger.info(f"🔄 Fetching onchain data from {url}")
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Successfully fetched data for {len(data)} coins")
            return data
        else:
            logger.error(f"❌ API request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error fetching onchain data: {e}")
        return None

def save_onchain_data(connection, data):
    """Save onchain data to database"""
    if not data:
        return
        
    cursor = connection.cursor()
    
    insert_sql = """
    INSERT INTO crypto_onchain_data (
        symbol, coin_id, market_cap, fully_diluted_valuation, total_volume,
        circulating_supply, total_supply, max_supply, ath, ath_date, atl, atl_date,
        price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
        market_cap_rank, market_cap_change_percentage_24h, volume_to_market_cap_ratio
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    records_saved = 0
    for coin in data:
        try:
            # Calculate volume to market cap ratio
            volume_to_mcap_ratio = None
            if coin.get('market_cap') and coin.get('total_volume'):
                volume_to_mcap_ratio = coin['total_volume'] / coin['market_cap']
            
            # Parse dates
            ath_date = None
            atl_date = None
            if coin.get('ath_date'):
                ath_date = datetime.fromisoformat(coin['ath_date'].replace('Z', '+00:00'))
            if coin.get('atl_date'):
                atl_date = datetime.fromisoformat(coin['atl_date'].replace('Z', '+00:00'))
            
            values = (
                coin.get('symbol', '').upper(),
                coin.get('id', ''),
                coin.get('market_cap'),
                coin.get('fully_diluted_valuation'),
                coin.get('total_volume'),
                coin.get('circulating_supply'),
                coin.get('total_supply'),
                coin.get('max_supply'),
                coin.get('ath'),
                ath_date,
                coin.get('atl'),
                atl_date,
                coin.get('price_change_percentage_24h'),
                coin.get('price_change_percentage_7d'),
                coin.get('price_change_percentage_30d'),
                coin.get('market_cap_rank'),
                coin.get('market_cap_change_percentage_24h'),
                volume_to_mcap_ratio
            )
            
            cursor.execute(insert_sql, values)
            records_saved += 1
            
        except Exception as e:
            logger.error(f"❌ Error saving data for {coin.get('id', 'unknown')}: {e}")
    
    connection.commit()
    cursor.close()
    logger.info(f"✅ Saved {records_saved} onchain records to database")

def main():
    """Main collector loop"""
    logger.info("🚀 Starting CoinGecko Onchain Data Collector")
    logger.info(f"📡 Using API endpoint: {BASE_URL}")
    logger.info(f"🔑 API key configured: {'Yes' if API_KEY else 'No'}")
    
    if not API_KEY:
        logger.error("❌ No API key configured. Set COINGECKO_API_KEY environment variable.")
        return
    
    try:
        # Get database connection
        connection = get_db_connection()
        
        # Create table if needed
        create_table_if_not_exists(connection)
        
        collection_count = 0
        
        while True:
            try:
                logger.info(f"🔄 Starting collection cycle #{collection_count + 1}")
                
                # Fetch onchain data
                onchain_data = fetch_onchain_data()
                
                if onchain_data:
                    # Save to database
                    save_onchain_data(connection, onchain_data)
                    collection_count += 1
                    logger.info(f"✅ Collection cycle #{collection_count} completed successfully")
                else:
                    logger.warning("⚠️ No data collected this cycle")
                
                # Wait before next collection (5 minutes for premium API)
                logger.info("⏰ Waiting 5 minutes before next collection...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"❌ Error in collection cycle: {e}")
                logger.info("⏰ Waiting 1 minute before retry...")
                time.sleep(60)
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logger.info("📫 Database connection closed")

if __name__ == '__main__':
    main()
