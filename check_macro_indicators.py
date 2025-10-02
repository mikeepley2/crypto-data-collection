#!/usr/bin/env python3

import mysql.connector


def main():
    conn = mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    cursor = conn.cursor()

    print('=== MACRO INDICATORS ANALYSIS ===')

    # Check DXY specifically
    cursor.execute("""
    SELECT indicator_name, indicator_date, value 
    FROM macro_indicators 
    WHERE indicator_name LIKE '%DXY%' OR indicator_name LIKE '%dxy%' 
    ORDER BY indicator_date DESC LIMIT 10
    """)
    dxy_data = cursor.fetchall()
    print('DXY data:')
    if dxy_data:
        for row in dxy_data:
            print(f'  {row}')
    else:
        print('  No DXY data found')

    # Get all indicators
    cursor.execute("SELECT DISTINCT indicator_name FROM macro_indicators ORDER BY indicator_name")
    indicators = cursor.fetchall()
    print(f'\nAll macro indicators ({len(indicators)} total):')
    for ind in indicators:
        print(f'  {ind[0]}')

    conn.close()


if __name__ == "__main__":
    main()