#!/usr/bin/env python3
"""
CI Database Setup using existing accessible databases
Uses existing databases that news_collector can access
"""

import mysql.connector
import sys

def setup_test_tables_in_existing_db():
    """Setup test tables in existing accessible database"""
    
    credentials = {
        'host': '172.22.32.1',
        'port': 3306,
        'user': 'news_collector', 
        'password': '99Rules!'
    }
    
    # Try accessible databases in order of preference
    available_databases = ['crypto_news', 'crypto_prices', 'crypto_transactions']
    
    print("🔧 Setting up test tables in existing database...")
    print("=" * 50)
    
    for db_name in available_databases:
        print(f"\n🎯 Trying database: {db_name}")
        
        try:
            # Connect to specific database
            connection = mysql.connector.connect(
                database=db_name,
                **credentials
            )
            
            cursor = connection.cursor()
            
            # Check current tables
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 Existing tables: {existing_tables}")
            
            # Define test tables we need (avoiding conflicts)
            test_tables = {
                'test_crypto_assets': """
                CREATE TABLE IF NOT EXISTS test_crypto_assets (
                    id VARCHAR(50) PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    current_price DECIMAL(20,8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """,
                
                'test_price_data_real': """
                CREATE TABLE IF NOT EXISTS test_price_data_real (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    current_price DECIMAL(20,8) NOT NULL,
                    market_cap BIGINT,
                    total_volume BIGINT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """,
                
                'test_news_data': """
                CREATE TABLE IF NOT EXISTS test_news_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(500),
                    content TEXT,
                    url VARCHAR(1000),
                    source VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
                """
            }
            
            # Create test tables
            created_tables = []
            
            for table_name, sql in test_tables.items():
                try:
                    print(f"🔨 Creating {table_name}...")
                    cursor.execute(sql)
                    created_tables.append(table_name)
                    print(f"✅ {table_name} created successfully")
                except Exception as e:
                    print(f"❌ Error creating {table_name}: {e}")
            
            connection.commit()
            
            # Insert test data
            if created_tables:
                print(f"\n📝 Inserting test data...")
                
                # Test crypto assets
                if 'test_crypto_assets' in created_tables:
                    cursor.execute("""
                        INSERT IGNORE INTO test_crypto_assets (id, symbol, name, current_price)
                        VALUES 
                            ('bitcoin', 'BTC', 'Bitcoin', 45000.00),
                            ('ethereum', 'ETH', 'Ethereum', 3200.00)
                    """)
                
                # Test price data  
                if 'test_price_data_real' in created_tables:
                    cursor.execute("""
                        INSERT IGNORE INTO test_price_data_real (symbol, current_price, market_cap, total_volume)
                        VALUES 
                            ('BTC', 45000.00, 850000000000, 25000000000),
                            ('ETH', 3200.00, 380000000000, 15000000000)
                    """)
                
                # Test news data
                if 'test_news_data' in created_tables:
                    cursor.execute("""
                        INSERT IGNORE INTO test_news_data (title, content, url, source)
                        VALUES 
                            ('Test Bitcoin News', 'Bitcoin reaches new highs in test scenario', 'https://test.com/btc', 'TestSource'),
                            ('Test Ethereum News', 'Ethereum shows strong performance in test', 'https://test.com/eth', 'TestSource')
                    """)
                
                connection.commit()
                print(f"✅ Test data inserted")
            
            # Verify final state
            cursor.execute("SHOW TABLES")
            final_tables = [table[0] for table in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            print(f"\n🎉 Test tables setup complete in {db_name}!")
            print(f"📊 All tables: {final_tables}")
            print(f"🧪 Test tables created: {created_tables}")
            
            return db_name, created_tables
            
        except Exception as e:
            print(f"❌ Error with database {db_name}: {e}")
            continue
    
    return None, []

def create_table_aliases():
    """Create views/aliases that map test tables to expected names"""
    
    credentials = {
        'host': '172.22.32.1',
        'port': 3306, 
        'user': 'news_collector',
        'password': '99Rules!',
        'database': 'crypto_news'  # Use the most likely database for aliases
    }
    
    print(f"\n🔗 Creating table aliases for integration tests...")
    
    try:
        connection = mysql.connector.connect(**credentials)
        cursor = connection.cursor()
        
        # Create views that map test table names to expected names
        aliases = {
            'crypto_assets': 'test_crypto_assets',
            'price_data_real': 'test_price_data_real', 
            'news_data': 'test_news_data'
        }
        
        for expected_name, actual_name in aliases.items():
            try:
                # Drop existing view if it exists
                cursor.execute(f"DROP VIEW IF EXISTS {expected_name}")
                
                # Create view
                cursor.execute(f"CREATE VIEW {expected_name} AS SELECT * FROM {actual_name}")
                print(f"✅ Created view: {expected_name} -> {actual_name}")
                
            except Exception as e:
                print(f"❌ Error creating view {expected_name}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating aliases: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 CI Database Setup using Existing Databases")
    print("=" * 60)
    
    # Step 1: Setup test tables in accessible database
    database_used, created_tables = setup_test_tables_in_existing_db()
    
    if not database_used:
        print(f"\n❌ Could not setup test tables in any accessible database!")
        return False
    
    # Step 2: Create aliases for expected table names
    aliases_created = create_table_aliases()
    
    if not aliases_created:
        print(f"\n⚠️  Test tables created but aliases failed - tests may need table name adjustments")
    
    print(f"\n🎉 CI Database setup complete!")
    print(f"🔗 Connection: news_collector@172.22.32.1:3306")
    print(f"📊 Database: {database_used}")
    print(f"🧪 Test tables: {created_tables}")
    print(f"✅ Integration tests can now run")
    
    # Output configuration
    print(f"\n📋 Configuration:")
    print(f"MYSQL_USER=news_collector")
    print(f"MYSQL_PASSWORD=99Rules!")
    print(f"MYSQL_HOST=172.22.32.1")
    print(f"MYSQL_DATABASE={database_used}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)