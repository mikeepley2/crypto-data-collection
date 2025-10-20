import mysql.connector
import statistics

conn = mysql.connector.connect(
    host="host.docker.internal",
    user="news_collector",
    password="99Rules!",
    database="crypto_news",
)
cursor = conn.cursor(dictionary=True)

# Get distribution of sentiment scores
cursor.execute(
    """
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN cryptobert_score > 0.5 THEN 1 ELSE 0 END) as very_positive,
        SUM(CASE WHEN cryptobert_score > 0 AND cryptobert_score <= 0.5 THEN 1 ELSE 0 END) as positive,
        SUM(CASE WHEN cryptobert_score = 0 THEN 1 ELSE 0 END) as neutral,
        SUM(CASE WHEN cryptobert_score >= -0.5 AND cryptobert_score < 0 THEN 1 ELSE 0 END) as negative,
        SUM(CASE WHEN cryptobert_score < -0.5 THEN 1 ELSE 0 END) as very_negative,
        MIN(cryptobert_score) as min_score,
        MAX(cryptobert_score) as max_score,
        AVG(cryptobert_score) as avg_score
    FROM crypto_sentiment_data
    WHERE cryptobert_score IS NOT NULL
"""
)

result = cursor.fetchone()
print("=" * 70)
print("SENTIMENT SCORE DISTRIBUTION ANALYSIS")
print("=" * 70)
print(f"\nTotal scores: {result['total']:,}")
print(f"\nScore Range: {result['min_score']:.3f} to {result['max_score']:.3f}")
print(f"Average: {result['avg_score']:.3f}")
print(f"\nDistribution:")

vpos = result["very_positive"] or 0
pos = result["positive"] or 0
neu = result["neutral"] or 0
neg = result["negative"] or 0
vneg = result["very_negative"] or 0

print(f"  Very Positive (>0.5):   {vpos:,} ({100*vpos/result['total']:.1f}%)")
print(f"  Positive (0 to 0.5):    {pos:,} ({100*pos/result['total']:.1f}%)")
print(f"  Neutral (0):            {neu:,} ({100*neu/result['total']:.1f}%)")
print(f"  Negative (-0.5 to 0):   {neg:,} ({100*neg/result['total']:.1f}%)")
print(f"  Very Negative (<-0.5):  {vneg:,} ({100*vneg/result['total']:.1f}%)")

# Get sample of different score ranges
print("\n" + "=" * 70)
print("SAMPLES FROM DIFFERENT SCORE RANGES")
print("=" * 70)

ranges = [
    ("Very Positive (>0.5)", "cryptobert_score > 0.5"),
    ("Positive (0-0.5)", "cryptobert_score > 0 AND cryptobert_score <= 0.5"),
    ("Neutral (0)", "cryptobert_score = 0"),
    ("Negative (-0.5 to 0)", "cryptobert_score >= -0.5 AND cryptobert_score < 0"),
    ("Very Negative (<-0.5)", "cryptobert_score < -0.5"),
]

for label, condition in ranges:
    print(f"\n{label}:")
    cursor.execute(
        f"""
        SELECT text, cryptobert_score 
        FROM crypto_sentiment_data 
        WHERE {condition}
        LIMIT 3
    """
    )
    for row in cursor.fetchall():
        text = row["text"][:70] if row["text"] else "N/A"
        print(f"  Score: {row['cryptobert_score']:7.3f} | {text}...")

conn.close()
print("\n✅ Analysis complete!")
