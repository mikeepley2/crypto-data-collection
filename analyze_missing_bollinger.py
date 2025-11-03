"""
Analyze why some Bollinger Bands records are missing
Investigate the 79,605 records that don't have Bollinger bands populated
"""

import mysql.connector
from datetime import datetime

config = {
    "host": "127.0.0.1",
    "user": "news_collector",
    "password": "99Rules!",
    "database": "crypto_prices",
}


def analyze_missing_bollinger():
    """Analyze why some records don't have Bollinger bands"""

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print("=" * 80)
        print("ANALYZING MISSING BOLLINGER BANDS")
        print("=" * 80)
        print()

        # 1. Total records and missing count
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN bollinger_upper IS NULL THEN 1 ELSE 0 END) as missing_upper,
            SUM(CASE WHEN bollinger_lower IS NULL THEN 1 ELSE 0 END) as missing_lower,
            SUM(CASE WHEN bollinger_upper IS NULL AND bollinger_lower IS NULL THEN 1 ELSE 0 END) as missing_both
        FROM technical_indicators
        """
        )

        result = cursor.fetchone()
        total = result[0]
        missing_upper = result[1]
        missing_lower = result[2]
        missing_both = result[3]

        print(f"Total technical records: {total:,}")
        print(f"Missing bollinger_upper: {missing_upper:,}")
        print(f"Missing bollinger_lower: {missing_lower:,}")
        print(f"Missing both: {missing_both:,}")
        print()

        # 2. Check if missing records have SMA_20 (required for Bollinger calculation)
        cursor.execute(
            """
        SELECT 
            COUNT(*) as missing_with_sma,
            COUNT(*) - SUM(CASE WHEN sma_20 IS NOT NULL THEN 1 ELSE 0 END) as missing_without_sma
        FROM technical_indicators
        WHERE bollinger_upper IS NULL
        """
        )

        sma_result = cursor.fetchone()
        missing_with_sma = sma_result[0] - sma_result[1]
        missing_without_sma = sma_result[1]

        print(f"Missing Bollinger records WITH SMA_20: {missing_with_sma:,}")
        print(f"Missing Bollinger records WITHOUT SMA_20: {missing_without_sma:,}")
        print()

        # 3. Check symbols with missing Bollinger bands
        cursor.execute(
            """
        SELECT 
            symbol,
            COUNT(*) as total_records,
            SUM(CASE WHEN bollinger_upper IS NULL THEN 1 ELSE 0 END) as missing_bb,
            MIN(timestamp_iso) as earliest,
            MAX(timestamp_iso) as latest
        FROM technical_indicators
        WHERE bollinger_upper IS NULL
        GROUP BY symbol
        ORDER BY missing_bb DESC
        LIMIT 20
        """
        )

        symbols = cursor.fetchall()
        print("TOP 20 SYMBOLS WITH MISSING BOLLINGER BANDS:")
        print("-" * 80)
        print(
            f"{'Symbol':<10} | {'Total':<8} | {'Missing':<8} | {'% Missing':<10} | {'Earliest':<12} | {'Latest':<12}"
        )
        print("-" * 80)

        for sym in symbols:
            pct = (sym[2] / sym[1] * 100) if sym[1] > 0 else 0
            earliest = str(sym[3])[:10] if sym[3] else "N/A"
            latest = str(sym[4])[:10] if sym[4] else "N/A"
            print(
                f"{sym[0]:<10} | {sym[1]:<8,} | {sym[2]:<8,} | {pct:<9.1f}% | {earliest:<12} | {latest:<12}"
            )

        print()

        # 4. Check if missing records have price data available
        cursor.execute(
            """
        SELECT 
            ti.symbol,
            COUNT(*) as missing_records,
            COUNT(pdr.symbol) as with_price_data,
            COUNT(*) - COUNT(pdr.symbol) as without_price_data
        FROM technical_indicators ti
        LEFT JOIN price_data_real pdr ON ti.symbol = pdr.symbol 
            AND pdr.timestamp < UNIX_TIMESTAMP(ti.timestamp_iso) * 1000
        WHERE ti.bollinger_upper IS NULL
        GROUP BY ti.symbol
        ORDER BY missing_records DESC
        LIMIT 10
        """
        )

        price_data = cursor.fetchall()
        print("PRICE DATA AVAILABILITY FOR MISSING RECORDS:")
        print("-" * 80)
        print(
            f"{'Symbol':<10} | {'Missing':<8} | {'With Price':<10} | {'Without Price':<13}"
        )
        print("-" * 80)

        for pd in price_data:
            print(f"{pd[0]:<10} | {pd[1]:<8,} | {pd[2]:<10,} | {pd[3]:<13,}")

        print()

        # 5. Check time distribution of missing records
        cursor.execute(
            """
        SELECT 
            DATE(timestamp_iso) as date,
            COUNT(*) as missing_count
        FROM technical_indicators
        WHERE bollinger_upper IS NULL
        GROUP BY DATE(timestamp_iso)
        ORDER BY date DESC
        LIMIT 10
        """
        )

        time_dist = cursor.fetchall()
        print("TIME DISTRIBUTION OF MISSING RECORDS:")
        print("-" * 40)
        print(f"{'Date':<12} | {'Missing Count':<15}")
        print("-" * 40)

        for td in time_dist:
            print(f"{str(td[0]):<12} | {td[1]:<15,}")

        print()

        # 6. Sample missing records for detailed analysis
        cursor.execute(
            """
        SELECT 
            id, symbol, timestamp_iso, sma_20,
            (SELECT COUNT(*) FROM price_data_real pdr 
             WHERE pdr.symbol = ti.symbol 
             AND pdr.timestamp < UNIX_TIMESTAMP(ti.timestamp_iso) * 1000) as price_count
        FROM technical_indicators ti
        WHERE bollinger_upper IS NULL
        ORDER BY timestamp_iso DESC
        LIMIT 5
        """
        )

        samples = cursor.fetchall()
        print("SAMPLE MISSING RECORDS:")
        print("-" * 80)
        print(
            f"{'ID':<8} | {'Symbol':<8} | {'Timestamp':<20} | {'SMA_20':<12} | {'Price Count':<12}"
        )
        print("-" * 80)

        for sample in samples:
            sma_val = f"{sample[3]:.4f}" if sample[3] else "NULL"
            print(
                f"{sample[0]:<8} | {sample[1]:<8} | {str(sample[2]):<20} | {sma_val:<12} | {sample[4]:<12}"
            )

        print()
        print("=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_missing_bollinger()




