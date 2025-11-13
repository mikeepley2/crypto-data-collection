import mysql.connector

config = {
    'host': '172.22.32.1',
    'port': 3306,
    'user': 'news_collector',
    'password': '99Rules!'
}

print("CORRECTED MIGRATION ANALYSIS")
print("=" * 60)

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# 1. Compare technical_indicators tables with correct column names
print("🔍 TECHNICAL_INDICATORS MIGRATION ANALYSIS:")
print("-" * 50)

# crypto_news version (uses timestamp and datetime_utc)
cursor.execute("USE crypto_news")
cursor.execute("SELECT MIN(datetime_utc), MAX(datetime_utc), COUNT(DISTINCT symbol) FROM technical_indicators WHERE datetime_utc IS NOT NULL")
news_min, news_max, news_symbols = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM technical_indicators")
news_total = cursor.fetchone()[0]

# crypto_prices version (uses timestamp_iso)
cursor.execute("USE crypto_prices")
cursor.execute("SELECT MIN(timestamp_iso), MAX(timestamp_iso), COUNT(DISTINCT symbol) FROM technical_indicators WHERE timestamp_iso IS NOT NULL")
prices_min, prices_max, prices_symbols = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM technical_indicators") 
prices_total = cursor.fetchone()[0]

print(f"crypto_news.technical_indicators ({news_total:,} rows):")
print(f"  Date range: {news_min} to {news_max}")
print(f"  Unique symbols: {news_symbols}")

print(f"crypto_prices.technical_indicators ({prices_total:,} rows):")
print(f"  Date range: {prices_min} to {prices_max}")
print(f"  Unique symbols: {prices_symbols}")

# Check for date overlap/gaps
migration_needed = False
if news_min and prices_min:
    if news_min < prices_min:
        print(f"⚠️  crypto_news has OLDER data: {news_min} vs {prices_min}")
        migration_needed = True
    elif news_max > prices_max:
        print(f"⚠️  crypto_news has NEWER data: {news_max} vs {prices_max}")
        migration_needed = True
    else:
        print(f"✅ crypto_prices covers the crypto_news date range")

# Check for unique symbols
cursor.execute("USE crypto_news")
cursor.execute("SELECT DISTINCT symbol FROM technical_indicators")
news_symbol_set = {row[0] for row in cursor.fetchall()}

cursor.execute("USE crypto_prices")
cursor.execute("SELECT DISTINCT symbol FROM technical_indicators")
prices_symbol_set = {row[0] for row in cursor.fetchall()}

unique_to_news = news_symbol_set - prices_symbol_set
unique_to_prices = prices_symbol_set - news_symbol_set

if unique_to_news:
    print(f"⚠️  Symbols ONLY in crypto_news: {sorted(list(unique_to_news))}")
    migration_needed = True
else:
    print("✅ No unique symbols in crypto_news")

print()

# 2. Analyze crypto_news tables
print("🔍 CRYPTO_NEWS TABLES ANALYSIS:")
print("-" * 50)

# Check different crypto_news tables
cursor.execute("USE crypto_news")
cursor.execute("SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM crypto_news WHERE created_at IS NOT NULL")
cn_count, cn_min, cn_max = cursor.fetchone()

cursor.execute("SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM crypto_news_data WHERE created_at IS NOT NULL")
cnd_count, cnd_min, cnd_max = cursor.fetchone()

cursor.execute("USE crypto_prices")
cursor.execute("SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM crypto_news WHERE created_at IS NOT NULL")
cp_count, cp_min, cp_max = cursor.fetchone()

print(f"crypto_news.crypto_news: {cn_count:,} records ({cn_min} to {cn_max})")
print(f"crypto_news.crypto_news_data: {cnd_count:,} records ({cnd_min} to {cnd_max})")
print(f"crypto_prices.crypto_news: {cp_count:,} records ({cp_min} to {cp_max})")

# Check for unique articles
cursor.execute("USE crypto_news")
cursor.execute("SELECT COUNT(DISTINCT title) FROM crypto_news")
cn_titles = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT title) FROM crypto_news_data")
cnd_titles = cursor.fetchone()[0]

cursor.execute("USE crypto_prices")
cursor.execute("SELECT COUNT(DISTINCT title) FROM crypto_news")
cp_titles = cursor.fetchone()[0]

print(f"\nUnique article titles:")
print(f"  crypto_news.crypto_news: {cn_titles:,}")
print(f"  crypto_news.crypto_news_data: {cnd_titles:,}")  
print(f"  crypto_prices.crypto_news: {cp_titles:,}")

news_migration_needed = cp_count < (cn_count + cnd_count)
if news_migration_needed:
    print("⚠️  crypto_news tables may contain additional data")
else:
    print("✅ crypto_prices.crypto_news appears to be the most complete")

print()

# 3. Generate migration plan
print("📋 MIGRATION PLAN:")
print("=" * 60)

if migration_needed:
    print("⚠️  MIGRATION REQUIRED for technical_indicators:")
    if unique_to_news:
        print(f"   • Migrate data for symbols: {sorted(list(unique_to_news))}")
    if news_min and prices_min and news_min < prices_min:
        print(f"   • Migrate older data from {news_min} to {prices_min}")
    print("   • Schema mapping needed (different column structures)")
else:
    print("✅ NO MIGRATION needed for technical_indicators")

if news_migration_needed:
    print("⚠️  POTENTIAL MIGRATION for crypto_news:")
    print("   • Verify unique articles before cleanup")
else:
    print("✅ NO MIGRATION needed for crypto_news")

print()
print("🎯 RECOMMENDED APPROACH:")
if migration_needed or news_migration_needed:
    print("1. Create migration scripts for unique data")
    print("2. Execute migrations with schema mapping")
    print("3. Verify data integrity") 
    print("4. Execute cleanup safely")
else:
    print("1. Verify no critical data in duplicates")
    print("2. Execute cleanup directly")
    print("3. Monitor for any missing functionality")

cursor.close()
conn.close()
