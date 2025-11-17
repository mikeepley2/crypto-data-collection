#!/usr/bin/env python3
"""
Investigate why data is missing in today's records
"""

import os
import mysql.connector
from datetime import datetime


def investigate_missing_data():
    """Investigate what data is available in source tables"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 INVESTIGATING MISSING DATA SOURCES")
        print("=" * 60)

        # Check today's price data
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM price_data_real 
            WHERE DATE(timestamp_iso) = CURDATE()
        """
        )
        today_prices = cursor.fetchone()[0]
        print(f"📊 Today's Price Records: {today_prices:,}")

        # Check technical indicators in price_data_real for today
        cursor.execute(
            """
            SELECT 
                COUNT(sma_20) as sma_count,
                COUNT(rsi_14) as rsi_count,
                COUNT(macd) as macd_count,
                COUNT(bb_upper) as bb_count
            FROM price_data_real 
            WHERE DATE(timestamp_iso) = CURDATE()
        """
        )
        tech_data = cursor.fetchone()
        print(f"📈 Technical Data in price_data_real:")
        print(f"  • SMA 20: {tech_data[0]:,}")
        print(f"  • RSI 14: {tech_data[1]:,}")
        print(f"  • MACD: {tech_data[2]:,}")
        print(f"  • Bollinger Bands: {tech_data[3]:,}")

        # Check onchain data for today
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM crypto_onchain_data 
            WHERE DATE(collection_date) = CURDATE()
        """
        )
        today_onchain = cursor.fetchone()[0]
        print(f"⛓️ Today's Onchain Records: {today_onchain:,}")

        if today_onchain > 0:
            cursor.execute(
                """
                SELECT 
                    COUNT(active_addresses_24h) as active_count,
                    COUNT(transaction_count_24h) as tx_count,
                    COUNT(exchange_net_flow_24h) as flow_count,
                    COUNT(price_volatility_7d) as vol_count
                FROM crypto_onchain_data 
                WHERE DATE(collection_date) = CURDATE()
            """
            )
            onchain_data = cursor.fetchone()
            print(f"⛓️ Onchain Data Available:")
            print(f"  • Active Addresses: {onchain_data[0]:,}")
            print(f"  • Transaction Count: {onchain_data[1]:,}")
            print(f"  • Exchange Net Flow: {onchain_data[2]:,}")
            print(f"  • Price Volatility: {onchain_data[3]:,}")

        # Check macro data
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM macro_indicators 
            WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """
        )
        recent_macro = cursor.fetchone()[0]
        print(f"🌍 Recent Macro Records (7 days): {recent_macro:,}")

        if recent_macro > 0:
            cursor.execute(
                """
                SELECT indicator_name, COUNT(*) as count
                FROM macro_indicators 
                WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY indicator_name
                ORDER BY count DESC
            """
            )
            macro_indicators = cursor.fetchall()
            print(f"🌍 Available Macro Indicators:")
            for name, count in macro_indicators:
                print(f"  • {name}: {count:,} records")

        # Check sentiment data for today
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM crypto_news 
            WHERE DATE(published_at) = CURDATE()
            AND ml_sentiment_score IS NOT NULL
        """
        )
        today_sentiment = cursor.fetchone()[0]
        print(f"💭 Today's Sentiment Records: {today_sentiment:,}")

        # Check what symbols we have today
        cursor.execute(
            """
            SELECT symbol, COUNT(*) as count
            FROM price_data_real 
            WHERE DATE(timestamp_iso) = CURDATE()
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """
        )
        today_symbols = cursor.fetchall()
        print(f"\n📊 Top 10 Symbols Today:")
        for symbol, count in today_symbols:
            print(f"  • {symbol}: {count:,} records")

        # Check if onchain data exists for today's symbols
        if today_symbols:
            sample_symbol = today_symbols[0][0].replace("-USD", "")
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM crypto_onchain_data 
                WHERE coin_symbol = %s 
                AND DATE(collection_date) = CURDATE()
            """,
                (sample_symbol,),
            )
            sample_onchain = cursor.fetchone()[0]
            print(
                f"\n🔍 Sample Check - {sample_symbol} onchain data today: {sample_onchain:,}"
            )

        # Check if technical data exists for today's symbols
        if today_symbols:
            sample_symbol = today_symbols[0][0]
            cursor.execute(
                """
                SELECT 
                    COUNT(sma_20) as sma_count,
                    COUNT(rsi_14) as rsi_count,
                    COUNT(macd) as macd_count
                FROM price_data_real 
                WHERE symbol = %s 
                AND DATE(timestamp_iso) = CURDATE()
            """,
                (sample_symbol,),
            )
            sample_tech = cursor.fetchone()
            print(f"🔍 Sample Check - {sample_symbol} technical data today:")
            print(f"  • SMA 20: {sample_tech[0]:,}")
            print(f"  • RSI 14: {sample_tech[1]:,}")
            print(f"  • MACD: {sample_tech[2]:,}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    investigate_missing_data()
