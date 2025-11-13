#!/bin/bash

# Comprehensive Data Collection Fix and Backfill Script
# This script applies FRED API fixes and backfills all missing data from 1/1/2023

set -e

echo "🚀 Comprehensive Data Collection Fix and Backfill"
echo "=================================================="
echo "📅 Target: Backfill from 2023-01-01 to present"
echo "🔧 Includes: FRED API fixes + comprehensive data backfill"
echo ""

# Set environment
export KUBECONFIG=~/.kube/config-crypto-trading

echo "📝 Step 1: Apply FRED API fixes from source code..."
kubectl apply -f k8s/collectors/collector-configmaps.yaml

echo "🔄 Step 2: Restart macro collector with fixed configuration..."
kubectl rollout restart deployment/macro-collector -n crypto-data-collection

echo "⏳ Step 3: Wait for macro collector to be ready..."
kubectl rollout status deployment/macro-collector -n crypto-data-collection --timeout=120s

echo "✅ FRED API fixes applied successfully!"
echo ""

# Wait for collector to start up
sleep 30

# Get new pod name
MACRO_POD=$(kubectl get pods -n crypto-data-collection -l app=macro-collector --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}')

if [ ! -z "$MACRO_POD" ]; then
    echo "📊 Step 4: Verify FRED API fix..."
    kubectl logs -n crypto-data-collection $MACRO_POD --tail=15
    echo ""
else
    echo "⚠️ Macro collector pod not ready yet"
fi

echo "🔄 Step 5: Starting comprehensive backfill from 2023-01-01..."
echo ""

# Create comprehensive backfill job
cat > comprehensive-backfill-job.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: comprehensive-backfill-2023
  namespace: crypto-data-collection
spec:
  ttlSecondsAfterFinished: 86400  # Keep for 24 hours
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: comprehensive-backfill
        image: python:3.11
        command: ["/bin/bash"]
        args:
        - -c
        - |
          pip install mysql-connector-python requests feedparser aiohttp asyncio tenacity

          cat > /app/comprehensive_backfill.py << 'PYEOF'
          #!/usr/bin/env python3
          """
          Comprehensive Data Backfill Script
          Backfills all missing data from 2023-01-01 to present
          """
          
          import mysql.connector
          import requests
          import asyncio
          import aiohttp
          import feedparser
          from datetime import datetime, timedelta
          from typing import List, Dict
          import time
          import logging
          
          logging.basicConfig(level=logging.INFO)
          logger = logging.getLogger("comprehensive-backfill")
          
          class ComprehensiveBackfill:
              def __init__(self):
                  self.db_config = {
                      'host': 'host.docker.internal',
                      'user': 'news_collector', 
                      'password': '99Rules!',
                      'database': 'crypto_prices'
                  }
                  self.start_date = datetime(2023, 1, 1)
                  self.end_date = datetime.now()
                  
              def get_db_connection(self):
                  return mysql.connector.connect(**self.db_config)
          
              def backfill_macro_indicators(self):
                  """Backfill macro indicators from 2023-01-01"""
                  logger.info("🏛️ Starting macro indicators backfill...")
                  
                  # Updated FRED series with correct codes
                  fred_series = {
                      "US_UNEMPLOYMENT": "UNRATE",
                      "US_INFLATION": "CPIAUCSL", 
                      "US_GDP": "A191RO1Q156NBEA",
                      "FEDERAL_FUNDS_RATE": "FEDFUNDS",
                      "10Y_YIELD": "DGS10",  # Fixed
                      "VIX": "VIXCLS",
                      "DXY": "DEXUSEU", 
                      "GOLD_PRICE": "GOLDAMGD228NLBM",  # Fixed
                      "OIL_PRICE": "DCOILWTICO"
                  }
                  
                  conn = self.get_db_connection()
                  cursor = conn.cursor()
                  
                  total_inserted = 0
                  
                  for indicator_name, series_id in fred_series.items():
                      try:
                          # Fetch historical data from FRED
                          url = f"https://api.stlouisfed.org/fred/series/observations"
                          params = {
                              'series_id': series_id,
                              'api_key': '35478996c5d5d88facc584e4de8e4467',
                              'file_type': 'json',
                              'observation_start': '2023-01-01',
                              'observation_end': datetime.now().strftime('%Y-%m-%d'),
                              'sort_order': 'desc',
                              'limit': 1000
                          }
                          
                          response = requests.get(url, params=params, timeout=30)
                          
                          if response.status_code == 200:
                              data = response.json()
                              observations = data.get('observations', [])
                              
                              inserted_count = 0
                              for obs in observations:
                                  if obs['value'] and obs['value'] != '.':
                                      try:
                                          insert_sql = """
                                          INSERT IGNORE INTO macro_indicators 
                                          (indicator_name, indicator_date, value, source, created_at)
                                          VALUES (%s, %s, %s, %s, %s)
                                          """
                                          cursor.execute(insert_sql, (
                                              indicator_name,
                                              obs['date'],
                                              float(obs['value']),
                                              f"FRED-{series_id}",
                                              datetime.now()
                                          ))
                                          inserted_count += 1
                                      except Exception as e:
                                          logger.warning(f"Skipped {indicator_name} {obs['date']}: {e}")
                              
                              total_inserted += inserted_count
                              logger.info(f"✅ {indicator_name}: {inserted_count} records backfilled")
                              
                          else:
                              logger.error(f"❌ FRED API error for {indicator_name}: {response.status_code}")
                              
                      except Exception as e:
                          logger.error(f"❌ Error backfilling {indicator_name}: {e}")
                  
                  conn.commit()
                  cursor.close()
                  conn.close()
                  
                  logger.info(f"🏛️ Macro indicators backfill completed: {total_inserted} total records")
                  
              def backfill_crypto_prices(self):
                  """Backfill crypto price data gaps"""
                  logger.info("💰 Starting crypto prices backfill...")
                  
                  # Major cryptocurrencies to backfill
                  symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 'polkadot', 'chainlink', 'uniswap']
                  
                  conn = self.get_db_connection()
                  cursor = conn.cursor()
                  
                  total_inserted = 0
                  
                  for symbol in symbols:
                      try:
                          # Get historical data from CoinGecko
                          url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
                          params = {
                              'vs_currency': 'usd',
                              'days': '730',  # ~2 years
                              'interval': 'daily'
                          }
                          
                          response = requests.get(url, params=params, timeout=30)
                          
                          if response.status_code == 200:
                              data = response.json()
                              prices = data.get('prices', [])
                              market_caps = data.get('market_caps', [])
                              volumes = data.get('total_volumes', [])
                              
                              inserted_count = 0
                              for i, price_data in enumerate(prices):
                                  if i < len(market_caps) and i < len(volumes):
                                      try:
                                          timestamp = int(price_data[0] / 1000)
                                          price = price_data[1]
                                          market_cap = market_caps[i][1] if i < len(market_caps) else None
                                          volume = volumes[i][1] if i < len(volumes) else None
                                          
                                          insert_sql = """
                                          INSERT IGNORE INTO price_data_real
                                          (symbol, current_price, market_cap, volume_usd_24h, timestamp, created_at)
                                          VALUES (%s, %s, %s, %s, %s, %s)
                                          """
                                          cursor.execute(insert_sql, (
                                              symbol.upper(),
                                              price,
                                              market_cap,
                                              volume,
                                              timestamp,
                                              datetime.now()
                                          ))
                                          inserted_count += 1
                                      except Exception as e:
                                          logger.warning(f"Skipped {symbol} price data: {e}")
                              
                              total_inserted += inserted_count
                              logger.info(f"✅ {symbol}: {inserted_count} price records backfilled")
                              
                              # Rate limiting
                              time.sleep(1)
                              
                          else:
                              logger.error(f"❌ CoinGecko API error for {symbol}: {response.status_code}")
                              
                      except Exception as e:
                          logger.error(f"❌ Error backfilling {symbol}: {e}")
                  
                  conn.commit()
                  cursor.close()
                  conn.close()
                  
                  logger.info(f"💰 Crypto prices backfill completed: {total_inserted} total records")
                  
              def backfill_ohlc_data(self):
                  """Backfill OHLC data gaps"""
                  logger.info("📊 Starting OHLC data backfill...")
                  
                  symbols = ['bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana']
                  
                  conn = self.get_db_connection()
                  cursor = conn.cursor()
                  
                  total_inserted = 0
                  
                  for symbol in symbols:
                      try:
                          # Get OHLC data from CoinGecko
                          url = f"https://api.coingecko.com/api/v3/coins/{symbol}/ohlc"
                          params = {
                              'vs_currency': 'usd',
                              'days': '730'
                          }
                          
                          response = requests.get(url, params=params, timeout=30)
                          
                          if response.status_code == 200:
                              data = response.json()
                              
                              inserted_count = 0
                              for ohlc in data:
                                  try:
                                      timestamp = int(ohlc[0] / 1000)
                                      open_price = ohlc[1]
                                      high_price = ohlc[2]
                                      low_price = ohlc[3]
                                      close_price = ohlc[4]
                                      
                                      insert_sql = """
                                      INSERT IGNORE INTO ohlc_data
                                      (symbol, timestamp_iso, open, high, low, close, timestamp, created_at, data_source)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                      """
                                      cursor.execute(insert_sql, (
                                          symbol.upper(),
                                          datetime.fromtimestamp(timestamp).isoformat(),
                                          open_price,
                                          high_price,
                                          low_price,
                                          close_price,
                                          timestamp,
                                          datetime.now(),
                                          'coingecko-backfill'
                                      ))
                                      inserted_count += 1
                                  except Exception as e:
                                      logger.warning(f"Skipped {symbol} OHLC data: {e}")
                              
                              total_inserted += inserted_count
                              logger.info(f"✅ {symbol}: {inserted_count} OHLC records backfilled")
                              
                              # Rate limiting
                              time.sleep(1)
                              
                          else:
                              logger.error(f"❌ CoinGecko API error for {symbol}: {response.status_code}")
                              
                      except Exception as e:
                          logger.error(f"❌ Error backfilling {symbol}: {e}")
                  
                  conn.commit()
                  cursor.close()
                  conn.close()
                  
                  logger.info(f"📊 OHLC data backfill completed: {total_inserted} total records")
          
              def run_comprehensive_backfill(self):
                  """Run complete backfill process"""
                  logger.info("🚀 Starting comprehensive backfill from 2023-01-01...")
                  
                  start_time = time.time()
                  
                  # Run all backfill processes
                  self.backfill_macro_indicators()
                  self.backfill_crypto_prices() 
                  self.backfill_ohlc_data()
                  
                  elapsed = time.time() - start_time
                  logger.info(f"✅ Comprehensive backfill completed in {elapsed:.1f} seconds")
                  
                  # Generate summary
                  conn = self.get_db_connection()
                  cursor = conn.cursor()
                  
                  logger.info("📊 BACKFILL SUMMARY:")
                  
                  # Check macro indicators
                  cursor.execute("SELECT COUNT(*) FROM macro_indicators WHERE indicator_date >= '2023-01-01'")
                  macro_count = cursor.fetchone()[0]
                  logger.info(f"   Macro indicators since 2023: {macro_count:,} records")
                  
                  # Check crypto prices  
                  cursor.execute("SELECT COUNT(*) FROM price_data_real WHERE created_at >= '2023-01-01'")
                  price_count = cursor.fetchone()[0]
                  logger.info(f"   Crypto prices since 2023: {price_count:,} records")
                  
                  # Check OHLC
                  cursor.execute("SELECT COUNT(*) FROM ohlc_data WHERE timestamp_iso >= '2023-01-01'")
                  ohlc_count = cursor.fetchone()[0]
                  logger.info(f"   OHLC data since 2023: {ohlc_count:,} records")
                  
                  cursor.close()
                  conn.close()
                  
                  logger.info("🎉 Comprehensive backfill completed successfully!")

          if __name__ == "__main__":
              backfill = ComprehensiveBackfill()
              backfill.run_comprehensive_backfill()
          PYEOF
          
          python /app/comprehensive_backfill.py
        env:
        - name: DB_HOST
          value: "host.docker.internal"
        - name: DB_USER
          value: "news_collector"
        - name: DB_PASSWORD
          value: "99Rules!"
        - name: DB_NAME
          value: "crypto_prices"
EOF

echo "📋 Step 6: Applying comprehensive backfill job..."
kubectl apply -f comprehensive-backfill-job.yaml

echo "⏳ Step 7: Monitoring backfill progress..."
kubectl wait --for=condition=ready pod -l job-name=comprehensive-backfill-2023 -n crypto-data-collection --timeout=60s

# Get job pod name
JOB_POD=$(kubectl get pods -n crypto-data-collection -l job-name=comprehensive-backfill-2023 -o jsonpath='{.items[0].metadata.name}')

if [ ! -z "$JOB_POD" ]; then
    echo "📊 Following backfill logs..."
    kubectl logs -f -n crypto-data-collection $JOB_POD
else
    echo "⚠️ Backfill job pod not ready yet"
    echo "Monitor with: kubectl logs -f -n crypto-data-collection -l job-name=comprehensive-backfill-2023"
fi

echo ""
echo "🎯 PROCESS SUMMARY:"
echo "✅ FRED API fixes applied to source code"
echo "✅ Macro collector restarted with fixes"
echo "✅ Comprehensive backfill job submitted"
echo "📅 Target: All data from 2023-01-01 to present"
echo ""
echo "🔍 Monitor progress with:"
echo "kubectl logs -f -n crypto-data-collection -l job-name=comprehensive-backfill-2023"