import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)
cursor = conn.cursor(dictionary=True)

cursor.execute(
    """SELECT COUNT(*) as cnt, 
    SUM(CASE WHEN avg_cryptobert_score IS NOT NULL THEN 1 ELSE 0 END) as with_sentiment 
    FROM ml_features_materialized"""
)
r = cursor.fetchone()

print("ML Features Sentiment Integration Status")
print("=" * 60)
print(f"Total ML feature records: {r['cnt']:,}")
print(f"With CryptoBERT sentiment: {r['with_sentiment']:,}")
if r['cnt'] > 0:
    pct = 100 * r['with_sentiment'] / r['cnt']
    print(f"Coverage: {pct:.1f}%")

conn.close()
