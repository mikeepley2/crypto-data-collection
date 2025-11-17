#!/usr/bin/env python3
"""
MySQL Database Analysis using K8s credentials
Analyzes all databases and technical indicators tables
"""

import mysql.connector
from datetime import datetime
import base64

def analyze_mysql_with_k8s_credentials():
    """Run MySQL analysis using credentials from K8s config"""
    
    # K8s Configuration from centralized config
    MYSQL_HOST = "localhost"  # Since MySQL is on Windows host
    MYSQL_PORT = 3306
    MYSQL_DATABASE = "crypto_prices"  # From centralized config
    MYSQL_USER = "news_collector"     # From centralized config  
    MYSQL_PASSWORD = "99Rules!"       # From secrets config
    
    print("🔍 MYSQL DATABASE ANALYSIS (using K8s credentials)")
    print("=" * 80)
    print(f"🗓️  Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Host: {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"👤 User: {MYSQL_USER}")
    print(f"🎯 Primary Database: {MYSQL_DATABASE}")
    print("=" * 80)
    
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            # Don't specify database initially to see all databases
        )
        
        cur = conn.cursor()
        print("✅ Successfully connected to MySQL!")
        print()
        
        # Step 1: List all databases
        print("📋 STEP 1: ALL DATABASES")
        print("-" * 50)
        cur.execute("SHOW DATABASES")
        databases = [db[0] for db in cur.fetchall()]
        
        for db in databases:
            if db not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                print(f"📊 {db}")
        
        print()
        
        # Step 2: Find all technical indicators tables across all databases
        print("🔍 STEP 2: TECHNICAL INDICATORS TABLES")
        print("-" * 80)
        
        cur.execute("""
            SELECT 
                table_schema AS database_name,
                table_name,
                COALESCE(table_rows, 0) AS estimated_rows,
                ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2) AS size_mb,
                create_time,
                update_time,
                CONCAT(table_schema, '.', table_name) AS full_table_name
            FROM information_schema.tables 
            WHERE (LOWER(table_name) LIKE '%technical%' 
                   OR LOWER(table_name) LIKE '%indicator%'
                   OR LOWER(table_name) LIKE '%tech%'
                   OR table_name LIKE 'tech_%')
               AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            ORDER BY estimated_rows DESC, size_mb DESC
        """)
        
        tech_tables = cur.fetchall()
        
        if not tech_tables:
            print("❌ No technical indicators tables found!")
        else:
            print(f"✅ Found {len(tech_tables)} technical indicators tables:")
            print()
            
            best_table = None
            best_score = 0
            
            for row in tech_tables:
                db_name, table_name, row_count, size_mb, create_time, update_time, full_name = row
                
                print(f"📊 {full_name}")
                print(f"   📈 Rows: {row_count:,}")
                print(f"   💾 Size: {size_mb:.2f} MB")
                print(f"   📅 Created: {create_time}" if create_time else "   📅 Created: Unknown")
                print(f"   🔄 Updated: {update_time}" if update_time else "   🔄 Updated: Unknown")
                
                # Calculate score (rows + size weight)
                score = row_count + (size_mb * 1000)
                print(f"   🏆 Score: {score:.0f}")
                
                if score > best_score:
                    best_score = score
                    best_table = {
                        'full_name': full_name,
                        'database': db_name,
                        'table': table_name,
                        'rows': row_count,
                        'size_mb': size_mb,
                        'score': score
                    }
                
                print()
        
        # Step 3: Find all crypto/ML related tables  
        print("📊 STEP 3: ALL CRYPTO/ML RELATED TABLES")
        print("-" * 80)
        
        cur.execute("""
            SELECT 
                table_schema AS database_name,
                table_name,
                COALESCE(table_rows, 0) AS estimated_rows,
                ROUND(COALESCE((data_length + index_length) / 1024 / 1024, 0), 2) AS size_mb,
                CONCAT(table_schema, '.', table_name) AS full_name
            FROM information_schema.tables 
            WHERE (LOWER(table_name) LIKE '%crypto%' 
                   OR LOWER(table_name) LIKE '%price%'
                   OR LOWER(table_name) LIKE '%market%'
                   OR LOWER(table_name) LIKE '%ml%'
                   OR LOWER(table_name) LIKE '%feature%'
                   OR LOWER(table_name) LIKE '%material%'
                   OR LOWER(table_name) LIKE '%btc%'
                   OR LOWER(table_name) LIKE '%eth%'
                   OR LOWER(table_name) LIKE '%sentiment%'
                   OR LOWER(table_name) LIKE '%news%')
               AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
            ORDER BY estimated_rows DESC, size_mb DESC
            LIMIT 20
        """)
        
        crypto_results = cur.fetchall()
        
        for row in crypto_results:
            db_name, table_name, row_count, size_mb, full_name = row
            print(f"📊 {full_name}")
            print(f"   📈 Rows: {row_count:,}")
            print(f"   💾 Size: {size_mb:.2f} MB")
            print()
        
        # Step 4: Recommendations
        print("🏆 RECOMMENDATIONS:")
        print("=" * 50)
        
        if best_table and tech_tables:
            print(f"✅ PRIMARY TABLE: {best_table['full_name']}")
            print(f"   📈 Rows: {best_table['rows']:,}")
            print(f"   💾 Size: {best_table['size_mb']:.2f} MB")
            print(f"   🏆 Score: {best_table['score']:.0f}")
            print()
            
            print("💡 RECOMMENDED ACTIONS:")
            print("1. ✅ Use this table as your primary technical indicators source")
            print("2. 🔄 Rename other technical tables to *_old")
            print("3. 📊 Verify data completeness and quality")
            print("4. 🔗 Update any references to point to this table")
            print()
            
            # Generate cleanup commands for other tables
            print("🔧 CLEANUP COMMANDS FOR OTHER TABLES:")
            print("-" * 50)
            for row in tech_tables:
                db_name, table_name, row_count, size_mb, create_time, update_time, full_name = row
                if full_name != best_table['full_name']:
                    print(f"USE {db_name}; RENAME TABLE {table_name} TO {table_name}_old;")
        else:
            print("❌ No technical indicators tables found!")
        
        print()
        print("🏁 DATABASE ANALYSIS COMPLETE")
        
        cur.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        print("💡 Check that MySQL is running and credentials are correct")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    analyze_mysql_with_k8s_credentials()