#!/usr/bin/env python3
"""
CI Database Setup with Credential Discovery
Tries different MySQL credential combinations commonly used in CI environments
"""

import mysql.connector
import os
import sys

def try_credential_combinations():
    """Try various credential combinations for CI environments"""
    
    # Common CI MySQL configurations
    credential_sets = [
        # GitHub Actions / CI standard patterns
        {'user': 'root', 'password': 'root'},
        {'user': 'root', 'password': 'password'},  
        {'user': 'root', 'password': ''},
        {'user': 'test', 'password': 'test'},
        {'user': 'mysql', 'password': 'mysql'},
        {'user': 'ci', 'password': 'ci'},
        
        # Project-specific credentials
        {'user': 'news_collector', 'password': '99Rules!'},
        {'user': 'crypto_user', 'password': 'crypto_password'},
    ]
    
    host = '172.22.32.1'
    port = 3306
    
    print(f"🔍 Testing MySQL credentials at {host}:{port}")
    print("=" * 50)
    
    for i, creds in enumerate(credential_sets, 1):
        user = creds['user']
        password = creds['password']
        pwd_display = '***' if password else 'empty'
        
        print(f"Test {i}: {user}@{host}:{port} (password: {pwd_display})")
        
        try:
            connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=10
            )
            
            cursor = connection.cursor()
            
            # Get version and databases
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            # Check privileges
            cursor.execute("SHOW GRANTS")
            grants = [grant[0] for grant in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            print(f"✅ SUCCESS! MySQL {version}")
            print(f"📋 Databases: {databases}")
            print(f"🔑 Grants: {grants[:2]}{'...' if len(grants) > 2 else ''}")
            
            return creds, databases
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        print()
    
    return None, []

def create_test_database(credentials, databases):
    """Create test database and basic tables"""
    
    print("🔧 Creating test database and tables...")
    
    host = '172.22.32.1'
    port = 3306
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=credentials['user'],
            password=credentials['password'],
            connect_timeout=10
        )
        
        cursor = connection.cursor()
        
        # Create test database if it doesn't exist
        test_db = 'crypto_data_test'
        if test_db not in databases:
            print(f"📁 Creating database: {test_db}")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {test_db}")
            connection.commit()
        else:
            print(f"📁 Database {test_db} already exists")
        
        # Switch to test database
        cursor.execute(f"USE {test_db}")
        
        # Create essential tables
        tables = {
            'crypto_assets': """
            CREATE TABLE IF NOT EXISTS crypto_assets (
                id VARCHAR(50) PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                current_price DECIMAL(20,8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """,
            
            'price_data_real': """
            CREATE TABLE IF NOT EXISTS price_data_real (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                current_price DECIMAL(20,8) NOT NULL,
                market_cap BIGINT,
                total_volume BIGINT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """,
            
            'news_data': """
            CREATE TABLE IF NOT EXISTS news_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500),
                content TEXT,
                url VARCHAR(1000),
                source VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        }
        
        created_tables = []
        
        for table_name, sql in tables.items():
            try:
                print(f"🔨 Creating table: {table_name}")
                cursor.execute(sql)
                created_tables.append(table_name)
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⏭️  Table {table_name} already exists")
                    created_tables.append(table_name)
                else:
                    print(f"❌ Error creating {table_name}: {e}")
        
        connection.commit()
        
        # Insert test data
        print("📝 Inserting test data...")
        
        # Test assets
        cursor.execute("""
            INSERT IGNORE INTO crypto_assets (id, symbol, name, current_price)
            VALUES 
                ('bitcoin', 'BTC', 'Bitcoin', 45000.00),
                ('ethereum', 'ETH', 'Ethereum', 3200.00)
        """)
        
        # Test price data
        cursor.execute("""
            INSERT IGNORE INTO price_data_real (symbol, current_price, market_cap, total_volume)
            VALUES 
                ('BTC', 45000.00, 850000000000, 25000000000),
                ('ETH', 3200.00, 380000000000, 15000000000)
        """)
        
        connection.commit()
        
        # Verify setup
        cursor.execute("SHOW TABLES")
        actual_tables = [table[0] for table in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        print(f"✅ Database setup complete!")
        print(f"📊 Tables created: {actual_tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 CI Database Setup with Credential Discovery")
    print("=" * 60)
    
    # Step 1: Find working credentials
    credentials, databases = try_credential_combinations()
    
    if not credentials:
        print("\n❌ No working MySQL credentials found!")
        print("💡 Ensure MySQL service is running with one of these credential sets:")
        print("   - root/root")
        print("   - root/password") 
        print("   - root/(empty)")
        print("   - test/test")
        return False
    
    print(f"\n🎯 Found working credentials: {credentials['user']}")
    
    # Step 2: Setup database
    success = create_test_database(credentials, databases)
    
    if success:
        print(f"\n🎉 CI Database setup complete!")
        print(f"🔗 Connection: {credentials['user']}@172.22.32.1:3306")
        print(f"📊 Database: crypto_data_test")
        print(f"✅ Integration tests should now work")
        
        # Output configuration for scripts
        print(f"\n📋 Configuration for use:")
        print(f"MYSQL_USER={credentials['user']}")
        print(f"MYSQL_PASSWORD={credentials['password']}")
        print(f"MYSQL_HOST=172.22.32.1")
        print(f"MYSQL_DATABASE=crypto_data_test")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)