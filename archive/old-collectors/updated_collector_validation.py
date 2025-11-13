
#!/usr/bin/env python3
import mysql.connector
import os
from datetime import datetime, timedelta

# Database connection using centralized config
conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
    port=int(os.getenv('MYSQL_PORT', 3306)),
    user=os.getenv('MYSQL_USER', 'news_collector'),
    password=os.getenv('MYSQL_PASSWORD', '99Rules!'),
    database=os.getenv('MYSQL_DATABASE', 'crypto_prices')
)

cursor = conn.cursor()
recent_threshold = datetime.now() - timedelta(hours=24)

print("📊 COLLECTOR HEALTH VALIDATION (Updated)")
print("=" * 60)

# Check each collector's target table with correct names
collectors = {
    "crypto-news-collector": "crypto_news",
    "enhanced-crypto-prices": "technical_indicators", 
    "onchain-collector": "crypto_onchain_data",
    "macro-collector": "macro_indicators", 
    "enhanced-sentiment-collector": "sentiment_aggregation",
    "technical-calculator": "technical_indicators"
}

health_scores = {}
for collector, table in collectors.items():
    try:
        # Get recent record count
        cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE timestamp_iso >= %s", (recent_threshold,))
        recent_count = cursor.fetchone()[0]
        
        # Get total records
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        total_count = cursor.fetchone()[0]
        
        # Get latest timestamp
        cursor.execute(f"SELECT MAX(timestamp_iso) FROM `{table}`")
        latest = cursor.fetchone()[0]
        
        # Calculate health score
        hours_ago = (datetime.now() - latest).total_seconds() / 3600 if latest else 999
        score = max(0, 100 - (hours_ago * 10))  # Lose 10 points per hour old
        
        health_scores[collector] = score
        
        print(f"\n{collector}:")
        print(f"  Table: {table}")
        print(f"  Total Records: {total_count:,}")
        print(f"  Recent (24h): {recent_count:,}")
        print(f"  Latest: {latest}")
        print(f"  Health Score: {score:.1f}/100")
        
    except Exception as e:
        print(f"\n{collector}: ERROR - {e}")
        health_scores[collector] = 0

cursor.close()
conn.close()

overall_health = sum(health_scores.values()) / len(health_scores)
print(f"\n🎯 OVERALL HEALTH SCORE: {overall_health:.1f}/100")
