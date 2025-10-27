#!/usr/bin/env python3
"""
Analyze sentiment data structure and coverage
Check for ML vs LLM scores, overall vs symbol-specific sentiment
"""

import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    database=os.environ["MYSQL_DATABASE"],
)
cursor = conn.cursor()

print("🔍 ANALYZING SENTIMENT DATA STRUCTURE")
print("=" * 60)

# Check 1: Sentiment table schema
print("📋 Sentiment Table Schema (crypto_news):")
cursor.execute("DESCRIBE crypto_news")
schema = cursor.fetchall()
for field, type_info, null, key, default, extra in schema:
    if "sentiment" in field.lower() or "score" in field.lower():
        print(f"   {field}: {type_info}")

# Check 2: Materialized table sentiment columns
print("\n📋 Materialized Table Sentiment Columns:")
cursor.execute("DESCRIBE ml_features_materialized")
schema = cursor.fetchall()
for field, type_info, null, key, default, extra in schema:
    if "sentiment" in field.lower() or "score" in field.lower():
        print(f"   {field}: {type_info}")

# Check 3: Check for ML vs LLM scores in crypto_news
print("\n🤖 ML vs LLM Score Analysis:")
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_articles,
        COUNT(ml_sentiment_score) as ml_scores,
        COUNT(sentiment_score) as llm_scores,
        COUNT(CASE WHEN ml_sentiment_score IS NOT NULL AND sentiment_score IS NOT NULL THEN 1 END) as both_scores
    FROM crypto_news
    WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
"""
)
score_counts = cursor.fetchone()
total, ml_scores, llm_scores, both_scores = score_counts
print(f"   Total articles (last 7 days): {total:,}")
print(f"   ML sentiment scores: {ml_scores:,} ({ml_scores/total*100:.1f}%)")
print(f"   LLM sentiment scores: {llm_scores:,} ({llm_scores/total*100:.1f}%)")
print(f"   Both ML and LLM: {both_scores:,} ({both_scores/total*100:.1f}%)")

# Check 4: Sample sentiment data
print("\n📊 Sample Sentiment Data:")
cursor.execute(
    """
    SELECT 
        title,
        ml_sentiment_score,
        sentiment_score,
        crypto_mentions
    FROM crypto_news
    WHERE ml_sentiment_score IS NOT NULL OR sentiment_score IS NOT NULL
    ORDER BY published_at DESC
    LIMIT 5
"""
)
samples = cursor.fetchall()
for title, ml_score, llm_score, mentions in samples:
    print(f"   Title: {title[:50]}...")
    print(f"   ML Score: {ml_score}, LLM Score: {llm_score}")
    print(f"   Mentions: {mentions}")
    print()

# Check 5: Check for overall vs symbol-specific sentiment
print("🎯 Overall vs Symbol-Specific Sentiment Analysis:")
cursor.execute(
    """
    SELECT 
        COUNT(*) as total_articles,
        COUNT(CASE WHEN crypto_mentions IS NULL OR crypto_mentions = '' THEN 1 END) as no_mentions,
        COUNT(CASE WHEN crypto_mentions IS NOT NULL AND crypto_mentions != '' THEN 1 END) as with_mentions
    FROM crypto_news
    WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (ml_sentiment_score IS NOT NULL OR sentiment_score IS NOT NULL)
"""
)
mention_counts = cursor.fetchone()
total_articles, no_mentions, with_mentions = mention_counts
print(f"   Total articles with sentiment: {total_articles:,}")
print(f"   No crypto mentions: {no_mentions:,} ({no_mentions/total_articles*100:.1f}%)")
print(
    f"   With crypto mentions: {with_mentions:,} ({with_mentions/total_articles*100:.1f}%)"
)

# Check 6: Current materialized table sentiment coverage
print("\n📈 Current Materialized Table Sentiment Coverage:")
cursor.execute("SELECT COUNT(*) FROM ml_features_materialized")
total_materialized = cursor.fetchone()[0]

cursor.execute(
    "SELECT COUNT(*) FROM ml_features_materialized WHERE avg_ml_overall_sentiment IS NOT NULL"
)
ml_sentiment_coverage = cursor.fetchone()[0]

print(f"   Total materialized records: {total_materialized:,}")
print(
    f"   With ML sentiment: {ml_sentiment_coverage:,} ({ml_sentiment_coverage/total_materialized*100:.1f}%)"
)

# Check 7: Check if we have overall sentiment scores
print("\n🌐 Overall Sentiment Analysis:")
cursor.execute(
    """
    SELECT 
        AVG(ml_sentiment_score) as avg_overall_ml,
        AVG(sentiment_score) as avg_overall_llm,
        COUNT(*) as count
    FROM crypto_news
    WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND (ml_sentiment_score IS NOT NULL OR sentiment_score IS NOT NULL)
"""
)
overall_sentiment = cursor.fetchone()
avg_ml, avg_llm, count = overall_sentiment
print(f"   Overall ML sentiment (last 7 days): {avg_ml:.3f} from {count:,} articles")
print(f"   Overall LLM sentiment (last 7 days): {avg_llm:.3f} from {count:,} articles")

# Check 8: Check for symbol-specific sentiment
print("\n🪙 Symbol-Specific Sentiment Analysis:")
cursor.execute(
    """
    SELECT 
        crypto_mentions,
        COUNT(*) as count,
        AVG(ml_sentiment_score) as avg_ml,
        AVG(sentiment_score) as avg_llm
    FROM crypto_news
    WHERE published_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND crypto_mentions IS NOT NULL 
    AND crypto_mentions != ''
    AND (ml_sentiment_score IS NOT NULL OR sentiment_score IS NOT NULL)
    GROUP BY crypto_mentions
    ORDER BY count DESC
    LIMIT 10
"""
)
symbol_sentiment = cursor.fetchall()
print("   Top symbols by sentiment volume:")
for mentions, count, avg_ml, avg_llm in symbol_sentiment:
    print(f"   {mentions}: {count} articles, ML: {avg_ml:.3f}, LLM: {avg_llm:.3f}")

conn.close()

print("\n" + "=" * 60)
print("🎯 RECOMMENDATIONS FOR SENTIMENT STRATEGY:")
print("=" * 60)
