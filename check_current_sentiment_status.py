import mysql.connector
from datetime import datetime, timedelta

conn = mysql.connector.connect(
    host="127.0.0.1", user="news_collector", password="99Rules!", database="crypto_news"
)
cursor = conn.cursor(dictionary=True)

print("=" * 70)
print("SENTIMENT SERVICE STATUS CHECK")
print("=" * 70)

# Get overall statistics
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as with_sentiment,
        COUNT(DISTINCT DATE(published_at)) as days_with_articles
    FROM crypto_sentiment_data
"""
)

stats = cursor.fetchone()
print(f"\nOverall Coverage:")
print(f"  Total Articles: {stats['total']:,}")
print(
    f"  With Sentiment: {stats['with_sentiment']:,} ({100*stats['with_sentiment']/stats['total']:.1f}%)"
)
print(f"  Days with Articles: {stats['days_with_articles']}")

# Get recent article processing stats
cursor.execute(
    """
    SELECT 
        DATE(published_at) as date,
        COUNT(*) as articles,
        SUM(CASE WHEN sentiment_score IS NOT NULL THEN 1 ELSE 0 END) as with_sentiment,
        SUM(CASE WHEN cryptobert_score IS NOT NULL AND cryptobert_score != 0 THEN 1 ELSE 0 END) as ml_processed
    FROM crypto_sentiment_data
    GROUP BY DATE(published_at)
    ORDER BY date DESC
    LIMIT 7
"""
)

print(f"\nLast 7 Days of Articles:")
print(f"{'Date':<12} {'Total':<8} {'Sentiment':<12} {'ML':<8}")
print("-" * 40)

for row in cursor.fetchall():
    date_str = row["date"].strftime("%Y-%m-%d") if row["date"] else "N/A"
    total = row["articles"] or 0
    sent = row["with_sentiment"] or 0
    ml = row["ml_processed"] or 0
    sent_pct = f"{100*sent/total:.0f}%" if total > 0 else "0%"
    ml_pct = f"{100*ml/total:.0f}%" if total > 0 else "0%"
    print(f"{date_str:<12} {total:<8} {sent} ({sent_pct:<5}) {ml} ({ml_pct:<5})")

# Get distribution of scores
cursor.execute(
    """
    SELECT 
        SUM(CASE WHEN cryptobert_score > 0.5 THEN 1 ELSE 0 END) as very_positive,
        SUM(CASE WHEN cryptobert_score > 0 AND cryptobert_score <= 0.5 THEN 1 ELSE 0 END) as positive,
        SUM(CASE WHEN cryptobert_score = 0 THEN 1 ELSE 0 END) as neutral,
        SUM(CASE WHEN cryptobert_score >= -0.5 AND cryptobert_score < 0 THEN 1 ELSE 0 END) as negative,
        SUM(CASE WHEN cryptobert_score < -0.5 THEN 1 ELSE 0 END) as very_negative
    FROM crypto_sentiment_data
    WHERE cryptobert_score IS NOT NULL
"""
)

dist = cursor.fetchone()
total_ml = sum(
    [
        dist["very_positive"] or 0,
        dist["positive"] or 0,
        dist["neutral"] or 0,
        dist["negative"] or 0,
        dist["very_negative"] or 0,
    ]
)

print(f"\nML Sentiment Distribution:")
print(
    f"  Very Positive (>0.5):   {dist['very_positive'] or 0:,} ({100*(dist['very_positive'] or 0)/total_ml:.1f}%)"
)
print(
    f"  Positive (0-0.5):       {dist['positive'] or 0:,} ({100*(dist['positive'] or 0)/total_ml:.1f}%)"
)
print(
    f"  Neutral (0):            {dist['neutral'] or 0:,} ({100*(dist['neutral'] or 0)/total_ml:.1f}%)"
)
print(
    f"  Negative (-0.5-0):      {dist['negative'] or 0:,} ({100*(dist['negative'] or 0)/total_ml:.1f}%)"
)
print(
    f"  Very Negative (<-0.5):  {dist['very_negative'] or 0:,} ({100*(dist['very_negative'] or 0)/total_ml:.1f}%)"
)

print("\n" + "=" * 70)
print("Status Check Complete")
print("=" * 70)

conn.close()
