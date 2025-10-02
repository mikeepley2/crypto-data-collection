#!/usr/bin/env python3
import mysql.connector

def check_technical_indicators():
    """Check technical indicators status after schema fixes"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    # Check for technical indicators in last hour
    cursor.execute('SELECT COUNT(*) as count FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)')
    recent = cursor.fetchone()['count']
    print(f'Technical indicators in last hour: {recent}')

    # Check latest technical indicators
    cursor.execute('SELECT symbol, timestamp, rsi_14, sma_20 FROM technical_indicators ORDER BY timestamp DESC LIMIT 5')
    latest = cursor.fetchall()
    print(f'Latest 5 technical indicators:')
    for row in latest:
        print(f'  {row["symbol"]}: {row["timestamp"]} - RSI: {row["rsi_14"]}, SMA20: {row["sma_20"]}')

    conn.close()

if __name__ == "__main__":
    check_technical_indicators()