#!/bin/bash
# Quick MySQL Test with Your Credentials
# Replace these with your actual MySQL credentials

echo "🔧 Testing MySQL with your actual credentials"
echo "============================================"

# Prompt for your MySQL credentials
read -p "Enter your MySQL username (or press Enter for 'root'): " mysql_user
mysql_user=${mysql_user:-root}

read -s -p "Enter your MySQL password: " mysql_password
echo ""

read -p "Enter your MySQL database name (or press Enter for 'crypto_data_test'): " mysql_db
mysql_db=${mysql_db:-crypto_data_test}

# Set environment variables
export MYSQL_HOST=172.22.32.1
export MYSQL_PORT=3306
export MYSQL_USER="$mysql_user"
export MYSQL_PASSWORD="$mysql_password"
export MYSQL_DATABASE="$mysql_db"

echo ""
echo "🧪 Testing connection with your credentials..."
echo "   Host: $MYSQL_HOST"
echo "   Port: $MYSQL_PORT"  
echo "   User: $MYSQL_USER"
echo "   Database: $MYSQL_DATABASE"

# Test the connection
python3 -c "
import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host='$MYSQL_HOST',
        port=int('$MYSQL_PORT'),
        user='$MYSQL_USER',
        password='$MYSQL_PASSWORD',
        database='$MYSQL_DATABASE'
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print('✅ Connection successful!')
        cursor.close()
        connection.close()
        
        # Run diagnostics with these settings
        print('')
        print('🔍 Running diagnostics with your settings...')
        
except Error as e:
    if 'Unknown database' in str(e):
        print('⚠️  Database does not exist. Trying without database...')
        try:
            connection = mysql.connector.connect(
                host='$MYSQL_HOST',
                port=int('$MYSQL_PORT'),
                user='$MYSQL_USER',
                password='$MYSQL_PASSWORD'
            )
            cursor = connection.cursor()
            print('✅ MySQL connection successful (without database)')
            print('📋 Available databases:')
            cursor.execute('SHOW DATABASES')
            for (db,) in cursor:
                print(f'   - {db}')
            
            print('')
            print('💡 To create the test database, run:')
            print('   CREATE DATABASE crypto_data_test;')
            
            cursor.close()
            connection.close()
        except Exception as e2:
            print(f'❌ Connection failed: {e2}')
    else:
        print(f'❌ Connection failed: {e}')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎯 Your MySQL settings are working!"
    echo "   You can now run tests with these environment variables:"
    echo "   export MYSQL_HOST=$MYSQL_HOST"
    echo "   export MYSQL_PORT=$MYSQL_PORT"
    echo "   export MYSQL_USER=$MYSQL_USER"
    echo "   export MYSQL_PASSWORD='$MYSQL_PASSWORD'"
    echo "   export MYSQL_DATABASE=$MYSQL_DATABASE"
    echo ""
    echo "🧪 Running diagnostic test..."
    python3 tests/test_environment_diagnostics.py
fi