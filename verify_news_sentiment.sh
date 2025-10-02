#!/bin/bash

echo "=== NEWS/SENTIMENT COLLECTION VERIFICATION ==="
echo "Checking deployment status..."

# Check pod status
kubectl get pods -n crypto-collectors | grep -E "(news|sentiment)"

echo ""
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=crypto-news-collector -n crypto-collectors --timeout=300s
kubectl wait --for=condition=ready pod -l app=simple-sentiment-collector -n crypto-collectors --timeout=300s

echo ""
echo "Checking health endpoints..."
kubectl exec -n crypto-collectors deployment/crypto-news-collector -- curl -s http://localhost:8000/health
kubectl exec -n crypto-collectors deployment/simple-sentiment-collector -- curl -s http://localhost:8000/health

echo ""
echo "Triggering manual collection..."
kubectl exec -n crypto-collectors deployment/crypto-news-collector -- curl -X POST http://localhost:8000/collect
kubectl exec -n crypto-collectors deployment/simple-sentiment-collector -- curl -X POST http://localhost:8000/collect

echo ""
echo "Checking data in database..."
kubectl exec -n crypto-collectors enhanced-crypto-prices-75584c468c-x7sb7 -- python -c "
import mysql.connector
conn = mysql.connector.connect(host='host.docker.internal', user='news_collector', password='99Rules!', database='crypto_news')
cursor = conn.cursor()

# Check recent news
cursor.execute('SELECT COUNT(*) FROM crypto_news_data WHERE DATE(created_at) = CURDATE()')
news_today = cursor.fetchone()[0]
print(f'News articles today: {news_today}')

# Check recent sentiment
for table in ['social_sentiment_data', 'stock_sentiment_data', 'crypto_sentiment_data']:
    cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE DATE(created_at) = CURDATE()')
    count = cursor.fetchone()[0]
    print(f'{table} today: {count}')

cursor.close()
conn.close()
"

echo ""
echo "=== VERIFICATION COMPLETE ==="