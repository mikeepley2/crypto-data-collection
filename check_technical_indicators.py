#!/usr/bin/env python3
import mysql.connector
import os

print('🔍 Checking technical indicators storage...')

# Database connection
config = {
    'host': 'host.docker.internal',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # Check recent technical indicators data
    cursor.execute('SELECT COUNT(*) FROM technical_indicators WHERE DATE(timestamp) >= "2025-09-26"')
    recent_count = cursor.fetchone()[0]

    cursor.execute('SELECT symbol, timestamp, rsi_14, sma_20, macd_line FROM technical_indicators WHERE DATE(timestamp) >= "2025-09-26" ORDER BY timestamp DESC LIMIT 5')
    recent_data = cursor.fetchall()

    print(f'Recent technical indicators (Sept 26): {recent_count}')
    if recent_data:
        print('Sample recent data:')
        for symbol, timestamp, rsi, sma, macd in recent_data:
            print(f'  {symbol} {timestamp}: RSI={rsi}, SMA20={sma}, MACD={macd}')
    else:
        print('No recent technical indicators data found')

    # Check what symbols have technical indicators
    cursor.execute('SELECT symbol, COUNT(*) as count FROM technical_indicators WHERE DATE(timestamp) >= "2025-09-25" GROUP BY symbol ORDER BY count DESC LIMIT 10')
    symbol_counts = cursor.fetchall()

    print()
    print('Top symbols with technical indicators (Sept 25+):')
    for symbol, count in symbol_counts:
        print(f'  {symbol}: {count} records')

    cursor.close()
    connection.close()
    print('✅ Technical indicators storage check complete!')

except Exception as e:
    print(f'❌ Error: {e}')