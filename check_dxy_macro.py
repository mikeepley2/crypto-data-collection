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

    print('=== MACRO INDICATORS DXY INVESTIGATION ===')

    # Check macro indicators table
    cursor.execute("SHOW TABLES LIKE '%macro%'")
    macro_tables = cursor.fetchall()
    print('Macro-related tables:')
    for table in macro_tables:
        print(f'  {table[0]}')

    if macro_tables:
        table_name = macro_tables[0][0]  # Use first macro table found
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        print(f'\nColumns in {table_name}:')
        for col in columns:
            print(f'  {col[0]} ({col[1]})')

        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample_data = cursor.fetchall()
        print(f'\nSample data from {table_name}:')
        for row in sample_data:
            print(f'  {row}')

        # Check for DXY specifically
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE indicator_name = 'dxy' OR indicator_name = 'DXY'")
        dxy_count = cursor.fetchone()[0]
        print(f'\nDXY records in {table_name}: {dxy_count}')

    conn.close()


if __name__ == "__main__":
    main()