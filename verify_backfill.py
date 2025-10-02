import mysql.connector
import os

# Connect to database
conn = mysql.connector.connect(
    host='host.docker.internal',
    user='news_collector', 
    password='99Rules!',
    database='crypto_news'
)

cursor = conn.cursor()

# Check total sentiment records
cursor.execute("SELECT COUNT(*) FROM social_sentiment_data")
total_records = cursor.fetchone()[0]
print(f"Total sentiment records: {total_records}")

# Check backfilled records
cursor.execute("SELECT COUNT(*) FROM social_sentiment_data WHERE collection_source = 'backfill_job'")
backfilled_records = cursor.fetchone()[0]
print(f"Backfilled records: {backfilled_records}")

# Check recent data
cursor.execute("SELECT DATE(timestamp) as date, COUNT(*) as count FROM social_sentiment_data GROUP BY DATE(timestamp) ORDER BY date DESC LIMIT 10")
recent_data = cursor.fetchall()
print(f"\nRecent data by date:")
for row in recent_data:
    print(f"  {row[0]}: {row[1]} records")

cursor.close()
conn.close()