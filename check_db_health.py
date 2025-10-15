#!/usr/bin/env python3

import mysql.connector
import os

def check_database_health():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'news_collector'),
            password=os.getenv('MYSQL_PASSWORD', '99Rules!'),
            database=os.getenv('MYSQL_DATABASE', 'crypto_prices')
        )
        
        cursor = conn.cursor()
        
        # Check connections
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        connections = cursor.fetchone()[1]
        
        # Check database size
        cursor.execute("""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
            FROM information_schema.tables 
            WHERE table_schema = %s
        """, (os.getenv('MYSQL_DATABASE', 'crypto_prices'),))
        db_size = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"Database Connections: {connections}")
        print(f"Database Size: {db_size} MB")
        
        # Calculate health score
        score = 100
        issues = []
        
        if int(connections) > 50:
            score -= 20
            issues.append(f"Too many connections: {connections}")
        
        if db_size > 10000:  # 10GB threshold
            score -= 10
            issues.append(f"Database too large: {db_size}MB")
        
        print(f"Health Score: {score}")
        if issues:
            print(f"Issues: {', '.join(issues)}")
        else:
            print("No issues found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database_health()
