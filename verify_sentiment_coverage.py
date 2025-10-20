import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1", user="news_collector", password="99Rules!", database="crypto_news"
)
cursor = conn.cursor(dictionary=True)

# Check sentiment coverage
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN cryptobert_score IS NOT NULL AND cryptobert_score != 0 THEN 1 ELSE 0 END) as with_cryptobert,
        SUM(CASE WHEN sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as with_traditional
    FROM crypto_sentiment_data
"""
)

result = cursor.fetchone()

print("=" * 70)
print("SENTIMENT COVERAGE VALIDATION")
print("=" * 70)
print(f"\nTotal records: {result['total']:,}")
print(
    f"With CryptoBERT: {result['with_cryptobert']:,} ({100*result['with_cryptobert']/result['total']:.1f}%)"
)
print(
    f"With Traditional: {result['with_traditional']:,} ({100*result['with_traditional']/result['total']:.1f}%)"
)

# Get sample stats
cursor.execute(
    """
    SELECT 
        MIN(cryptobert_score) as min_score,
        MAX(cryptobert_score) as max_score,
        AVG(cryptobert_score) as avg_score,
        STDDEV(cryptobert_score) as std_score
    FROM crypto_sentiment_data
    WHERE cryptobert_score IS NOT NULL
"""
)

stats = cursor.fetchone()
if stats["avg_score"] is not None:
    print(f"\nScore Statistics:")
    print(f"  Min: {stats['min_score']:.3f}")
    print(f"  Max: {stats['max_score']:.3f}")
    print(f"  Avg: {stats['avg_score']:.3f}")
    print(f"  StdDev: {stats['std_score']:.3f}")

print("\n" + "=" * 70)
print("Verification Complete!")
print("=" * 70)

conn.close()
