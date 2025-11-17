#!/usr/bin/env python3
"""
Comprehensive Database Discovery
Run the SQL analysis across all accessible databases to find any technical_indicators tables
"""
import mysql.connector
import sys
from contextlib import contextmanager

# Database credentials from K8s config
MYSQL_HOST = "172.22.32.1"
MYSQL_PORT = 3306
MYSQL_USER = "news_collector"
MYSQL_PASSWORD = "99Rules!"

@contextmanager
def mysql_connection(database=None):
    """Context manager for MySQL connections"""
    connection = None
    try:
        config = {
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'autocommit': True,
            'charset': 'utf8mb4',
            'use_unicode': True
        }
        if database:
            config['database'] = database
            
        connection = mysql.connector.connect(**config)
        yield connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def run_comprehensive_analysis():
    """Run comprehensive database and table analysis"""
    
    with mysql_connection() as conn:
        cursor = conn.cursor()
        
        print("🔍 COMPREHENSIVE DATABASE DISCOVERY")
        print("=" * 60)
        
        # Get all databases
        print("\n📊 ALL DATABASES ON SERVER:")
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        
        user_databases = [db for db in databases if db not in 
                         ['information_schema', 'performance_schema', 'mysql', 'sys']]
        
        for db in databases:
            marker = "🔥" if db in user_databases else "⚙️"
            print(f"  {marker} {db}")
        
        print(f"\n📈 User Databases Found: {len(user_databases)}")
        print(f"📈 User Database Names: {', '.join(user_databases)}")
        
        # Find all technical indicators tables
        print("\n🎯 SEARCHING FOR TECHNICAL_INDICATORS TABLES:")
        cursor.execute("""
        SELECT 
            table_schema as database_name,
            table_name,
            table_rows as estimated_rows,
            ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb,
            create_time,
            update_time
        FROM information_schema.tables 
        WHERE LOWER(table_name) LIKE '%technical%'
           AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
        ORDER BY table_schema, table_name
        """)
        
        tech_tables = cursor.fetchall()
        if tech_tables:
            for row in tech_tables:
                db_name, table_name, rows, size_mb, created, updated = row
                print(f"  📊 {db_name}.{table_name}")
                print(f"     ├─ Rows: {rows:,} | Size: {size_mb:.1f} MB")
                created_str = str(created) if created else "None"
                updated_str = str(updated) if updated else "None"
                print(f"     └─ Created: {created_str} | Updated: {updated_str}")
        else:
            print("  ❌ No technical_indicators tables found")
        
        # Find all crypto/market related tables 
        print("\n🚀 ALL CRYPTO/MARKET RELATED TABLES:")
        cursor.execute("""
        SELECT 
            table_schema as database_name,
            table_name,
            table_rows as estimated_rows,
            ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb
        FROM information_schema.tables 
        WHERE (LOWER(table_name) LIKE '%crypto%' 
               OR LOWER(table_name) LIKE '%price%'
               OR LOWER(table_name) LIKE '%market%'
               OR LOWER(table_name) LIKE '%onchain%'
               OR LOWER(table_name) LIKE '%ohlc%'
               OR LOWER(table_name) LIKE '%macro%'
               OR LOWER(table_name) LIKE '%technical%'
               OR LOWER(table_name) LIKE '%ml%'
               OR LOWER(table_name) LIKE '%sentiment%')
           AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
        ORDER BY table_schema, table_rows DESC
        """)
        
        all_tables = cursor.fetchall()
        current_db = None
        for row in all_tables:
            db_name, table_name, rows, size_mb = row
            if db_name != current_db:
                print(f"\n  🗄️  Database: {db_name}")
                current_db = db_name
            # Handle None values
            rows_str = f"{rows:,}" if rows is not None else "Unknown"
            size_str = f"{size_mb:.1f}" if size_mb is not None else "Unknown"
            print(f"     📊 {table_name}: {rows_str} rows ({size_str} MB)")
        
        # Check for specific databases the user mentioned
        print("\n🔍 CHECKING FOR SPECIFIC DATABASES MENTIONED BY USER:")
        expected_dbs = ['crypto_market_data', 'crypto_trading']
        for expected_db in expected_dbs:
            if expected_db in databases:
                print(f"  ✅ Found: {expected_db}")
            else:
                print(f"  ❌ Not Found: {expected_db}")
        
        # Show server information
        print(f"\n🖥️  MySQL SERVER INFO:")
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"  📦 Version: {version}")
        
        cursor.execute("SELECT @@hostname")
        hostname = cursor.fetchone()[0]
        print(f"  🏠 Hostname: {hostname}")
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.schemata")
        total_dbs = cursor.fetchone()[0]
        print(f"  📊 Total Databases: {total_dbs}")
        
        cursor.close()

if __name__ == "__main__":
    try:
        run_comprehensive_analysis()
        print("\n✅ Comprehensive analysis completed!")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)