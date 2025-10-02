#!/usr/bin/env python3
import mysql.connector
import os

print('🔧 Adding missing technical indicator columns...')

# Database connection
config = {
    'host': 'host.docker.internal',
    'user': 'root', 
    'password': '99Rules!',
    'database': 'crypto_prices'
}

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Add missing columns that the technical indicators service is trying to use
    missing_columns = [
        'atr_14',      # Average True Range 14 periods
        'bb_bandwidth', # Bollinger Band Bandwidth
        'kc_upper',    # Keltner Channel Upper
        'kc_lower',    # Keltner Channel Lower
        'kc_middle',   # Keltner Channel Middle
        'donchian_upper', # Donchian Channel Upper
        'donchian_lower', # Donchian Channel Lower
        'donchian_middle', # Donchian Channel Middle
        'ichimoku_base',   # Ichimoku Base Line
        'ichimoku_conversion', # Ichimoku Conversion Line
        'ichimoku_span_a',     # Ichimoku Span A
        'ichimoku_span_b',     # Ichimoku Span B
    ]

    for column in missing_columns:
        try:
            alter_sql = f"ALTER TABLE technical_indicators ADD COLUMN {column} DECIMAL(20,8) DEFAULT NULL"
            cursor.execute(alter_sql)
            print(f"✅ Added column: {column}")
        except mysql.connector.Error as e:
            if "Duplicate column name" in str(e):
                print(f"⚠️  Column already exists: {column}")
            else:
                print(f"❌ Error adding {column}: {e}")

    connection.commit()
    cursor.close()
    connection.close()
    print('✅ Technical indicator columns added successfully!')

except Exception as e:
    print(f'❌ Error: {e}')