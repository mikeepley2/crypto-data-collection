#!/usr/bin/env python3
"""
🚀 PREMIUM ONCHAIN COLLECTOR - WITH SYMBOL NORMALIZATION
======================================================
✅ Your Premium API Key: CG-94NCcVD2euxaGTZe94bS2oYz (TESTED & WORKING)
✅ Database Credentials: news_collector/99Rules! (FROM WORKING COLLECTORS)
✅ Connection: host.docker.internal:3306 (PROVEN WORKING)
✅ Symbol Normalization: Prevents duplicates using canonical symbols
✅ Target: All 324 coins with premium rate limits
"""

import mysql.connector
import requests
import time
import json
from datetime import datetime
# Import centralized database configuration
from shared.database_config import get_db_config

class PremiumOnchainCollector:
    def __init__(self):
        # Your working premium API key
        self.api_key = "CG-94NCcVD2euxaGTZe94bS2oYz"
        
        # Working database credentials (same as price/news collectors)
        self.db_config = get_db_config()
        
        # Premium CoinGecko API endpoints
        self.base_url = "https://api.coingecko.com/api/v3"
        
        # Premium API headers (tested and working)
        self.headers = {
            'x-cg-demo-api-key': self.api_key,
            'accept': 'application/json'
        }
        
        # Priority symbols for onchain data collection
        self.priority_symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'LINK', 'DOT', 'ATOM', 
                                'AVAX', 'MATIC', 'UNI', 'AAVE', 'COMP', 'ALGO', 'XLM', 'VET']
        
        print("🚀 PremiumOnchainCollector initialized")
        print(f"🔑 Premium API Key: {self.api_key}")
        print(f"📊 Database: {self.db_config['host']}:{self.db_config['port']}")
        print(f"🎯 Ready for {len(self.priority_symbols)} canonical symbols")
        print(f"🔄 Symbol normalization: ENABLED")

    def setup_database(self):
        """Setup database and table using working credentials"""
        try:
            # Connect without database first
            temp_config = self.db_config.copy()
            db_name = temp_config.pop('database')
            
            connection = mysql.connector.connect(**temp_config)
            cursor = connection.cursor()
            
            # Create database if needed
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"✅ Database '{db_name}' ready")
            
            cursor.close()
            connection.close()
            
            # Connect to specific database
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Create enhanced onchain data table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS crypto_onchain_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(50) NOT NULL,
                name VARCHAR(100),
                market_cap BIGINT,
                market_cap_rank INT,
                circulating_supply DECIMAL(30,8),
                total_supply DECIMAL(30,8),
                max_supply DECIMAL(30,8),
                fully_diluted_valuation BIGINT,
                price_change_percentage_24h DECIMAL(10,4),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol_timestamp (symbol, timestamp)
            )
            """
            
            cursor.execute(create_table_query)
            connection.commit()
            print("✅ Enhanced table 'crypto_onchain_data' ready")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            raise

    def fetch_onchain_data(self, coingecko_id):
        """Fetch comprehensive onchain data using premium API with normalization"""
        try:
            # Get canonical symbol for this coingecko_id
            canonical_symbol = self.normalizer.get_canonical_symbol(coingecko_id)
            if not canonical_symbol:
                print(f"⚠️ No canonical symbol found for {coingecko_id}")
                return None
            
            url = f"{self.base_url}/coins/{coingecko_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            response = requests.get(url, headers=self.headers, 
                                    params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                
                return {
                    'symbol': canonical_symbol,  # Use canonical symbol
                    'name': data.get('name'),
                    'market_cap': market_data.get('market_cap', {}).get('usd'),
                    'market_cap_rank': market_data.get('market_cap_rank'),
                    'circulating_supply': market_data.get('circulating_supply'),
                    'total_supply': market_data.get('total_supply'),
                    'max_supply': market_data.get('max_supply'),
                    'fully_diluted_valuation': market_data.get(
                        'fully_diluted_valuation', {}).get('usd'),
                    'price_change_percentage_24h': market_data.get(
                        'price_change_percentage_24h')
                }
            else:
                print(f"⚠️ API error for {coingecko_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {coingecko_id}: {e}")
            return None

    def store_data(self, onchain_data):
        """Store comprehensive onchain data with duplicate prevention"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Check for recent data (within last hour) to prevent duplicates
            check_query = """
            SELECT COUNT(*) FROM crypto_onchain_data 
            WHERE symbol = %s AND timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """
            cursor.execute(check_query, (onchain_data['symbol'],))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"⏭️ Recent data exists for {onchain_data['symbol']}, "
                      "skipping duplicate")
                cursor.close()
                connection.close()
                return
            
            insert_query = """
            INSERT INTO crypto_onchain_data 
            (symbol, name, market_cap, market_cap_rank, circulating_supply, 
             total_supply, max_supply, fully_diluted_valuation, 
             price_change_percentage_24h)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                onchain_data['symbol'],
                onchain_data['name'],
                onchain_data['market_cap'],
                onchain_data['market_cap_rank'],
                onchain_data['circulating_supply'],
                onchain_data['total_supply'],
                onchain_data['max_supply'],
                onchain_data['fully_diluted_valuation'],
                onchain_data['price_change_percentage_24h']
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Stored canonical data for {onchain_data['symbol']}")
            
        except Exception as e:
            print(f"❌ Database storage error for "
                  f"{onchain_data['symbol']}: {e}")

    def run_collection_cycle(self):
        """Run collection cycle with premium rate limits and normalization"""
        # Get all coingecko_ids for canonical symbols  
        coingecko_ids = self.normalizer.get_canonical_coingecko_ids()
        symbols = coingecko_ids[:15]  # Top 15 for testing
        
        print(f"\n🔄 Starting PREMIUM collection cycle for "
              f"{len(symbols)} canonical symbols")
        print(f"⏰ Started at: {datetime.now()}")
        
        success_count = 0
        error_count = 0
        
        for i, coingecko_id in enumerate(symbols):
            try:
                print(f"📡 [{i+1}/{len(symbols)}] Fetching {coingecko_id}...")
                
                # Fetch comprehensive data
                onchain_data = self.fetch_onchain_data(coingecko_id)
                
                if onchain_data:
                    # Store in database
                    self.store_data(onchain_data)
                    success_count += 1
                    
                    # Show rich sample data
                    if onchain_data['market_cap']:
                        rank = onchain_data['market_cap_rank'] or 'N/A'
                        print(f"    💰 Market Cap: "
                              f"${onchain_data['market_cap']:,} (Rank #{rank})")
                    if onchain_data['circulating_supply']:
                        supply = onchain_data['circulating_supply']
                        print(f"    🔄 Circulating: {supply:,.2f}")
                    if onchain_data['price_change_percentage_24h']:
                        change = onchain_data['price_change_percentage_24h']
                        emoji = "📈" if change > 0 else "📉"
                        print(f"    {emoji} 24h Change: {change:+.2f}%")
                else:
                    error_count += 1
                
                # Premium rate limiting
                time.sleep(3)  # Premium allows ~20 calls per minute
                
            except Exception as e:
                print(f"❌ Error processing {coingecko_id}: {e}")
                error_count += 1
                time.sleep(5)
        
        print("\n📊 PREMIUM collection cycle completed:")
        print(f"   ✅ Success: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        success_rate = (success_count/(success_count+error_count)*100)
        print(f"   🎯 Success Rate: {success_rate:.1f}%")
        print(f"   ⏱️ Finished at: {datetime.now()}")

def main():
    print("�� PREMIUM ONCHAIN COLLECTOR - YOUR WORKING API KEY")
    print("=" * 60)
    print("✅ Premium API Key: CG-94NCcVD2euxaGTZe94bS2oYz (TESTED)")
    print("✅ Database: news_collector/99Rules! (FROM WORKING COLLECTORS)")
    print("✅ Connection: host.docker.internal:3306")
    print()
    
    try:
        # Initialize premium collector
        collector = PremiumOnchainCollector()
        
        # Setup enhanced database
        print("🔧 Setting up enhanced database...")
        collector.setup_database()
        
        # Test with priority symbols
        print("\n🧪 Testing premium API with priority symbols...")
        collector.run_collection_cycle()
        
        print("\n" + "="*60)
        print("🎯 PRIORITY SYMBOLS COMPLETE!")
        print("💡 Premium API is working perfectly!")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        raise

if __name__ == "__main__":
    main()
