import mysql.connector

connection = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_prices'
)
print("Connected to database")

cursor = connection.cursor()

# Check real_time_sentiment_signals data with correct column names
cursor.execute("""
    SELECT 
        COUNT(*) as total_signals,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(timestamp) as earliest_timestamp,
        MAX(timestamp) as latest_timestamp,
        AVG(sentiment_score) as avg_sentiment,
        AVG(confidence) as avg_confidence
    FROM real_time_sentiment_signals
""")

result = cursor.fetchone()
if result:
    total, unique_symbols, earliest, latest, avg_sentiment, avg_confidence = result
    print(f"REAL_TIME_SENTIMENT_SIGNALS:")
    print(f"  Total signals: {total:,}")
    print(f"  Unique symbols: {unique_symbols}")
    print(f"  Timeframe: {earliest} to {latest}")
    print(f"  Avg sentiment: {avg_sentiment:.3f}" if avg_sentiment else "  Avg sentiment: None")
    print(f"  Avg confidence: {avg_confidence:.3f}" if avg_confidence else "  Avg confidence: None")

# Check BTC specific data
cursor.execute("""
    SELECT 
        COUNT(*) as btc_signals,
        MIN(timestamp) as btc_earliest,
        MAX(timestamp) as btc_latest,
        AVG(sentiment_score) as btc_avg_sentiment,
        COUNT(DISTINCT signal_type) as signal_types
    FROM real_time_sentiment_signals 
    WHERE symbol = 'BTC'
""")

btc_result = cursor.fetchone()
if btc_result:
    btc_count, btc_earliest, btc_latest, btc_sentiment, signal_types = btc_result
    print(f"  BTC signals: {btc_count:,}")
    if btc_count > 0:
        print(f"  BTC timeframe: {btc_earliest} to {btc_latest}")
        print(f"  BTC avg sentiment: {btc_sentiment:.3f}" if btc_sentiment else "  BTC avg sentiment: None")
        print(f"  BTC signal types: {signal_types}")

# Check sentiment_aggregation data
cursor.execute("DESCRIBE sentiment_aggregation")
agg_columns = [col[0] for col in cursor.fetchall()]
print(f"\nSENTIMENT_AGGREGATION columns: {agg_columns}")

cursor.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as unique_symbols,
        MIN(aggregation_date) as earliest_date,
        MAX(aggregation_date) as latest_date
    FROM sentiment_aggregation
""")

result = cursor.fetchone()
if result:
    total, unique_symbols, earliest, latest = result
    print(f"  Total records: {total:,}")
    print(f"  Unique symbols: {unique_symbols}")
    print(f"  Date range: {earliest} to {latest}")

# Check current ml_features_materialized sentiment fields
cursor.execute("DESCRIBE ml_features_materialized")
all_columns = [col[0] for col in cursor.fetchall()]

sentiment_fields = [col for col in all_columns if any(keyword in col.lower() for keyword in ['sentiment', 'social', 'news', 'reddit', 'twitter', 'fear', 'greed', 'buzz'])]

print(f"\nML_FEATURES sentiment fields ({len(sentiment_fields)}): {sentiment_fields}")

# Check current population
if sentiment_fields:
    field_checks = [f"SUM(CASE WHEN {field} IS NOT NULL THEN 1 ELSE 0 END) as {field}_count" for field in sentiment_fields[:5]]
    
    query = f"SELECT COUNT(*) as total, {', '.join(field_checks)} FROM ml_features_materialized"
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    total_symbols = result[0]
    print(f"\nSentiment field population (out of {total_symbols} symbols):")
    for i, field in enumerate(sentiment_fields[:5]):
        count = result[i + 1]
        print(f"  {field}: {count} ({count/total_symbols*100:.1f}%)")

cursor.close()
connection.close()