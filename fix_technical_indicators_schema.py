#!/usr/bin/env python3
import mysql.connector
import os

print('🔧 Fixing Technical Indicators Database Schema...')

# Database connection using technical indicators service credentials
config = {
    'host': 'host.docker.internal',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

# All potential missing columns that technical indicators service might need
missing_columns = [
    'true_range',           # True Range for ATR calculation
    'bb_width',            # Bollinger Band Width 
    'atr_14',              # 14-period Average True Range
    'bb_bandwidth',        # Bollinger Band Bandwidth (alternative name)
    'kc_upper',            # Keltner Channel Upper
    'kc_lower',            # Keltner Channel Lower  
    'kc_middle',           # Keltner Channel Middle
    'donchian_upper',      # Donchian Channel Upper
    'donchian_lower',      # Donchian Channel Lower
    'donchian_middle',     # Donchian Channel Middle
    'ichimoku_base',       # Ichimoku Base Line
    'ichimoku_conversion', # Ichimoku Conversion Line
    'ichimoku_span_a',     # Ichimoku Span A
    'ichimoku_span_b',     # Ichimoku Span B
    'cci_14',              # 14-period Commodity Channel Index
    'stoch_rsi_k',         # Stochastic RSI %K
    'stoch_rsi_d',         # Stochastic RSI %D
    'trix',                # TRIX indicator
    'aroon_up',            # Aroon Up
    'aroon_down',          # Aroon Down
    'adl',                 # Accumulation/Distribution Line (alternative)
    'cmf',                 # Chaikin Money Flow
    'volume_profile',      # Volume Profile
    'pvt',                 # Price Volume Trend (alternative)
    'nvi',                 # Negative Volume Index (alternative)
    'pvi'                  # Positive Volume Index (alternative)
]

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    added_count = 0
    exists_count = 0
    
    print('🔍 Checking existing columns...')
    cursor.execute('DESCRIBE technical_indicators')
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    print(f'Found {len(existing_columns)} existing columns')
    
    for column in missing_columns:
        if column in existing_columns:
            print(f'⚠️  Column already exists: {column}')
            exists_count += 1
        else:
            try:
                alter_sql = f"ALTER TABLE technical_indicators ADD COLUMN {column} DECIMAL(20,8) DEFAULT NULL"
                cursor.execute(alter_sql)
                connection.commit()
                print(f"✅ Added column: {column}")
                added_count += 1
            except mysql.connector.Error as e:
                if "Duplicate column name" in str(e):
                    print(f"⚠️  Column already exists: {column}")
                    exists_count += 1
                else:
                    print(f"❌ Error adding {column}: {e}")

    print(f'\n📊 Summary:')
    print(f'  ✅ Added: {added_count} columns')
    print(f'  ⚠️  Already existed: {exists_count} columns')
    print(f'  🔧 Total processed: {len(missing_columns)} columns')
    
    # Get final column count
    cursor.execute('SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "technical_indicators" AND TABLE_SCHEMA = "crypto_prices"')
    total_columns = cursor.fetchone()[0]
    print(f'  📈 Final column count: {total_columns}')

    cursor.close()
    connection.close()
    print('✅ Technical indicators schema fix completed!')

except Exception as e:
    print(f'❌ Error: {e}')