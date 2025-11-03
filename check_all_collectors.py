#!/usr/bin/env python3
"""Check all base collectors are working and data is populated"""
import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("BASE COLLECTORS STATUS CHECK")
print("=" * 80)
print()

# 1. PRICE COLLECTOR
print("1️⃣  PRICE COLLECTOR")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT symbol) as symbols,
        MIN(timestamp_iso) as earliest,
        MAX(timestamp_iso) as latest,
        MAX(timestamp_iso) as most_recent
    FROM price_data_real
"""
)
price_stats = cursor.fetchone()
print(f"   Total records: {price_stats['total']:,}")
print(f"   Unique symbols: {price_stats['symbols']}")
print(f"   Date range: {price_stats['earliest']} to {price_stats['latest']}")
print(f"   Most recent: {price_stats['most_recent']}")

# Check recent activity (last 6 hours)
recent_cutoff = datetime.now() - timedelta(hours=6)
cursor.execute(
    """
    SELECT COUNT(*) as recent_count
    FROM price_data_real
    WHERE timestamp_iso >= %s
""",
    (recent_cutoff,),
)
recent_price = cursor.fetchone()["recent_count"]
print(f"   Records in last 6 hours: {recent_price:,}")

if price_stats["most_recent"]:
    age_minutes = (datetime.now() - price_stats["most_recent"]).total_seconds() / 60
    if age_minutes < 60:
        print(f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)")
    elif age_minutes < 180:
        print(f"   ⚠️  Status: SLOW (last update {age_minutes:.0f} minutes ago)")
    else:
        print(f"   ❌ Status: STALE (last update {age_minutes:.0f} minutes ago)")
print()

# 2. TECHNICAL INDICATORS CALCULATOR
print("2️⃣  TECHNICAL INDICATORS CALCULATOR")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT symbol) as symbols,
        MIN(timestamp_iso) as earliest,
        MAX(timestamp_iso) as latest,
        MAX(timestamp_iso) as most_recent
    FROM technical_indicators
"""
)
tech_stats = cursor.fetchone()
print(f"   Total records: {tech_stats['total']:,}")
print(f"   Unique symbols: {tech_stats['symbols']}")
print(f"   Date range: {tech_stats['earliest']} to {tech_stats['latest']}")
print(f"   Most recent: {tech_stats['most_recent']}")

cursor.execute(
    """
    SELECT COUNT(*) as recent_count
    FROM technical_indicators
    WHERE timestamp_iso >= %s
""",
    (recent_cutoff,),
)
recent_tech = cursor.fetchone()["recent_count"]
print(f"   Records in last 6 hours: {recent_tech:,}")

# Check data completeness
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(rsi_14) as has_rsi,
        COUNT(sma_20) as has_sma,
        COUNT(macd) as has_macd,
        COUNT(bb_upper) as has_bb
    FROM technical_indicators
    WHERE timestamp_iso >= %s
""",
    (recent_cutoff,),
)
tech_comp = cursor.fetchone()
if tech_comp["total"] > 0:
    print(
        f"   Completeness (last 6h): RSI={tech_comp['has_rsi']/tech_comp['total']*100:.1f}%, SMA={tech_comp['has_sma']/tech_comp['total']*100:.1f}%, MACD={tech_comp['has_macd']/tech_comp['total']*100:.1f}%"
    )

if tech_stats["most_recent"]:
    age_minutes = (datetime.now() - tech_stats["most_recent"]).total_seconds() / 60
    if age_minutes < 60:
        print(f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)")
    elif age_minutes < 180:
        print(f"   ⚠️  Status: SLOW (last update {age_minutes:.0f} minutes ago)")
    else:
        print(f"   ❌ Status: STALE (last update {age_minutes:.0f} minutes ago)")
print()

# 3. MACRO COLLECTOR
print("3️⃣  MACRO COLLECTOR")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT indicator_name) as indicators,
        MIN(indicator_date) as earliest,
        MAX(indicator_date) as latest,
        MAX(indicator_date) as most_recent
    FROM macro_indicators
"""
)
macro_stats = cursor.fetchone()
print(f"   Total records: {macro_stats['total']:,}")
print(f"   Unique indicators: {macro_stats['indicators']}")
print(f"   Date range: {macro_stats['earliest']} to {macro_stats['latest']}")

# Get indicator names
cursor.execute(
    """
    SELECT DISTINCT indicator_name 
    FROM macro_indicators 
    ORDER BY indicator_name
"""
)
indicators = [r["indicator_name"] for r in cursor.fetchall()]
print(
    f"   Indicators: {', '.join(indicators[:10])}{'...' if len(indicators) > 10 else ''}"
)

# Check recent (last 7 days)
recent_date = datetime.now().date() - timedelta(days=7)
cursor.execute(
    """
    SELECT COUNT(DISTINCT indicator_date) as recent_dates
    FROM macro_indicators
    WHERE indicator_date >= %s
""",
    (recent_date,),
)
recent_macro_dates = cursor.fetchone()["recent_dates"]
print(f"   Dates with data (last 7 days): {recent_macro_dates}")

if macro_stats["most_recent"]:
    age_days = (datetime.now().date() - macro_stats["most_recent"]).days
    if age_days == 0:
        print(f"   ✅ Status: ACTIVE (data for today)")
    elif age_days <= 2:
        print(
            f"   ⚠️  Status: SLOW (most recent {age_days} days ago - may be FRED API delay)"
        )
    else:
        print(f"   ❌ Status: STALE (most recent {age_days} days ago)")
print()

# 4. ONCHAIN COLLECTOR
print("4️⃣  ONCHAIN COLLECTOR")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT coin_symbol) as symbols,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        MAX(timestamp) as most_recent
    FROM crypto_onchain_data
"""
)
onchain_stats = cursor.fetchone()
print(f"   Total records: {onchain_stats['total']:,}")
print(f"   Unique symbols: {onchain_stats['symbols']}")
print(f"   Date range: {onchain_stats['earliest']} to {onchain_stats['latest']}")
print(f"   Most recent: {onchain_stats['most_recent']}")

cursor.execute(
    """
    SELECT COUNT(*) as recent_count
    FROM crypto_onchain_data
    WHERE timestamp >= %s
""",
    (recent_cutoff,),
)
recent_onchain = cursor.fetchone()["recent_count"]
print(f"   Records in last 6 hours: {recent_onchain:,}")

# Check data completeness
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(active_addresses_24h) as has_addresses,
        COUNT(transaction_count_24h) as has_txs,
        COUNT(exchange_net_flow_24h) as has_flow
    FROM crypto_onchain_data
    WHERE timestamp >= %s
""",
    (recent_cutoff,),
)
onchain_comp = cursor.fetchone()
if onchain_comp["total"] > 0:
    print(
        f"   Completeness (last 6h): Addresses={onchain_comp['has_addresses']/onchain_comp['total']*100:.1f}%, Txs={onchain_comp['has_txs']/onchain_comp['total']*100:.1f}%, Flow={onchain_comp['has_flow']/onchain_comp['total']*100:.1f}%"
    )

if onchain_stats["most_recent"]:
    age_minutes = (datetime.now() - onchain_stats["most_recent"]).total_seconds() / 60
    if age_minutes < 360:
        print(f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)")
    elif age_minutes < 720:
        print(f"   ⚠️  Status: SLOW (last update {age_minutes:.0f} minutes ago)")
    else:
        print(f"   ❌ Status: STALE (last update {age_minutes:.0f} minutes ago)")
print()

# 5. OHLC DATA
print("5️⃣  OHLC DATA")
print("-" * 80)
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT symbol) as symbols,
        MIN(timestamp_iso) as earliest,
        MAX(timestamp_iso) as latest,
        MAX(timestamp_iso) as most_recent
    FROM ohlc_data
"""
)
ohlc_stats = cursor.fetchone()
print(f"   Total records: {ohlc_stats['total']:,}")
print(f"   Unique symbols: {ohlc_stats['symbols']}")
if ohlc_stats["earliest"]:
    print(f"   Date range: {ohlc_stats['earliest']} to {ohlc_stats['latest']}")
    print(f"   Most recent: {ohlc_stats['most_recent']}")

    cursor.execute(
        """
        SELECT COUNT(*) as recent_count
        FROM ohlc_data
        WHERE timestamp_iso >= %s
    """,
        (recent_cutoff,),
    )
    recent_ohlc = cursor.fetchone()["recent_count"]
    print(f"   Records in last 6 hours: {recent_ohlc:,}")

    if ohlc_stats["most_recent"]:
        age_minutes = (datetime.now() - ohlc_stats["most_recent"]).total_seconds() / 60
        if age_minutes < 1440:
            print(f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)")
        else:
            print(f"   ⚠️  Status: STALE (last update {age_minutes:.0f} minutes ago)")
else:
    print("   ❌ Status: NO DATA")
print()

# 6. NEWS COLLECTOR (if available)
print("6️⃣  NEWS COLLECTOR")
print("-" * 80)
try:
    cursor.execute(
        """
        SELECT COUNT(*) as cnt
        FROM information_schema.tables 
        WHERE table_schema = 'crypto_news' 
        AND table_name = 'crypto_news_data'
    """
    )
    news_table_exists = cursor.fetchone()["cnt"] > 0

    if news_table_exists:
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                MIN(published_at) as earliest,
                MAX(published_at) as latest,
                MAX(published_at) as most_recent
            FROM crypto_news.crypto_news_data
        """
        )
        news_stats = cursor.fetchone()
        print(f"   Total records: {news_stats['total']:,}")
        if news_stats["earliest"]:
            print(f"   Date range: {news_stats['earliest']} to {news_stats['latest']}")
            print(f"   Most recent: {news_stats['most_recent']}")

            if news_stats["most_recent"]:
                age_minutes = (
                    datetime.now() - news_stats["most_recent"]
                ).total_seconds() / 60
                if age_minutes < 120:
                    print(
                        f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)"
                    )
                else:
                    print(
                        f"   ⚠️  Status: SLOW (last update {age_minutes:.0f} minutes ago)"
                    )
        else:
            print("   ❌ Status: NO DATA")
    else:
        print("   ⚠️  Table not found (may be in different schema)")
except Exception as e:
    print(f"   ⚠️  Could not check: {e}")
print()

# 7. SENTIMENT COLLECTOR
print("7️⃣  SENTIMENT COLLECTOR")
print("-" * 80)
try:
    cursor.execute(
        """
        SELECT COUNT(*) as cnt
        FROM information_schema.tables 
        WHERE table_schema = 'crypto_news' 
        AND table_name = 'crypto_sentiment_data'
    """
    )
    sent_table_exists = cursor.fetchone()["cnt"] > 0

    if sent_table_exists:
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                MIN(published_at) as earliest,
                MAX(published_at) as latest,
                MAX(published_at) as most_recent
            FROM crypto_news.crypto_sentiment_data
        """
        )
        sent_stats = cursor.fetchone()
        print(f"   Total records: {sent_stats['total']:,}")
        if sent_stats["earliest"]:
            print(f"   Date range: {sent_stats['earliest']} to {sent_stats['latest']}")
            print(f"   Most recent: {sent_stats['most_recent']}")

            # Check recent
            cursor.execute(
                """
                SELECT COUNT(*) as recent_count
                FROM crypto_news.crypto_sentiment_data
                WHERE published_at >= %s
            """,
                (recent_cutoff,),
            )
            recent_sent = cursor.fetchone()["recent_count"]
            print(f"   Records in last 6 hours: {recent_sent:,}")

            if sent_stats["most_recent"]:
                age_minutes = (
                    datetime.now() - sent_stats["most_recent"]
                ).total_seconds() / 60
                if age_minutes < 120:
                    print(
                        f"   ✅ Status: ACTIVE (last update {age_minutes:.0f} minutes ago)"
                    )
                elif age_minutes < 360:
                    print(
                        f"   ⚠️  Status: SLOW (last update {age_minutes:.0f} minutes ago)"
                    )
                else:
                    print(
                        f"   ❌ Status: STALE (last update {age_minutes:.0f} minutes ago)"
                    )
        else:
            print("   ❌ Status: NO DATA")
    else:
        print("   ⚠️  Table not found (may be in different schema)")
except Exception as e:
    print(f"   ⚠️  Could not check: {e}")
print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)

collectors_status = []
if price_stats["total"] > 0 and recent_price > 0:
    collectors_status.append("✅ Price")
else:
    collectors_status.append("❌ Price")

if tech_stats["total"] > 0 and recent_tech > 0:
    collectors_status.append("✅ Technical")
else:
    collectors_status.append("❌ Technical")

if macro_stats["total"] > 0:
    collectors_status.append("✅ Macro")
else:
    collectors_status.append("❌ Macro")

if onchain_stats["total"] > 0 and recent_onchain > 0:
    collectors_status.append("✅ Onchain")
else:
    collectors_status.append("❌ Onchain")

print(f"Collectors: {', '.join(collectors_status)}")
print()

# Check if data is recent
print("Recent Activity (last 6 hours):")
print(f"  Price: {recent_price:,} records")
print(f"  Technical: {recent_tech:,} records")
print(f"  Onchain: {recent_onchain:,} records")
print()

conn.close()

