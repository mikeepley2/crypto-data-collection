#!/bin/bash

echo "🚀 Deploying Enhanced Collectors to K8s..."

# Apply just the deployments (without services/configmaps due to quotas)
echo "📦 Deploying enhanced crypto news collector..."
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-crypto-news-updated
  namespace: crypto-data-collection
  labels:
    app: enhanced-crypto-news
    component: data-collection
    version: enhanced
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enhanced-crypto-news
  template:
    metadata:
      labels:
        app: enhanced-crypto-news
        component: data-collection
        version: enhanced
    spec:
      nodeSelector:
        node-type: data-collection
      tolerations:
        - key: "data-platform"
          operator: "Equal"
          value: "true"
          effect: "NoSchedule"
      containers:
        - name: enhanced-crypto-news
          image: python:3.11-slim
          command: ["/bin/bash", "-c"]
          args:
            - |
              pip install mysql-connector-python requests fastapi uvicorn feedparser beautifulsoup4 python-dateutil
              
              # Create enhanced crypto news collector
              cat > /app/enhanced_crypto_news_collector.py << 'PYEOF'
              #!/usr/bin/env python3
              import os, logging, time, requests, mysql.connector, feedparser, re
              from datetime import datetime, timedelta
              from bs4 import BeautifulSoup
              from typing import List, Dict, Optional
              
              logging.basicConfig(level=logging.INFO)
              logger = logging.getLogger(__name__)
              
              class EnhancedCryptoNewsCollector:
                  def __init__(self):
                      self.db_config = {
                          "host": os.getenv("MYSQL_HOST", "host.docker.internal"),
                          "port": int(os.getenv("MYSQL_PORT", "3306")),
                          "user": os.getenv("MYSQL_USER", "news_collector"),
                          "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
                          "database": os.getenv("MYSQL_DATABASE", "crypto_prices")
                      }
                      
                      self.rss_feeds = [
                          "https://cointelegraph.com/rss",
                          "https://feeds.feedburner.com/CoinDesk",
                          "https://cryptonews.net/news/feed/",
                          "https://decrypt.co/feed",
                          "https://bitcoinist.com/feed/"
                      ]
                      
                      self.crypto_keywords = [
                          "bitcoin", "btc", "ethereum", "eth", "cryptocurrency", "crypto",
                          "blockchain", "defi", "nft", "altcoin", "cardano", "ada",
                          "solana", "sol", "polkadot", "dot", "chainlink", "link"
                      ]
                      
                  def get_db_connection(self):
                      return mysql.connector.connect(**self.db_config)
                      
                  def extract_sentiment_score(self, title: str, content: str) -> float:
                      positive_words = ["surge", "rise", "gain", "bull", "pump", "moon", "breakthrough", "adoption", "bullish"]
                      negative_words = ["crash", "drop", "fall", "bear", "dump", "decline", "bearish", "sell-off", "plunge"]
                      
                      text = f"{title} {content}".lower()
                      pos_count = sum(1 for word in positive_words if word in text)
                      neg_count = sum(1 for word in negative_words if word in text)
                      
                      if pos_count + neg_count == 0:
                          return 0.0
                      return (pos_count - neg_count) / max(pos_count + neg_count, 1)
                      
                  def fetch_rss_articles(self, feed_url: str) -> List[Dict]:
                      try:
                          response = requests.get(feed_url, timeout=30)
                          response.raise_for_status()
                          
                          feed = feedparser.parse(response.content)
                          articles = []
                          
                          for entry in feed.entries[:10]:
                              try:
                                  title = entry.get("title", "")
                                  content = entry.get("summary", "")
                                  
                                  if any(keyword in title.lower() or keyword in content.lower() for keyword in self.crypto_keywords):
                                      published = entry.get("published_parsed")
                                      if published:
                                          pub_date = datetime(*published[:6])
                                      else:
                                          pub_date = datetime.now()
                                          
                                      articles.append({
                                          "title": title,
                                          "content": content,
                                          "url": entry.get("link", ""),
                                          "source": feed_url,
                                          "published_at": pub_date,
                                          "sentiment_score": self.extract_sentiment_score(title, content)
                                      })
                                      
                              except Exception as e:
                                  logger.error(f"Error processing entry: {e}")
                                  continue
                                  
                          return articles
                          
                      except Exception as e:
                          logger.error(f"Error fetching {feed_url}: {e}")
                          return []
                          
                  def store_articles(self, articles: List[Dict]) -> int:
                      stored = 0
                      
                      try:
                          with self.get_db_connection() as conn:
                              cursor = conn.cursor()
                              
                              for article in articles:
                                  try:
                                      cursor.execute("""
                                          INSERT INTO crypto_news (
                                              title, content, url, source, published_at, sentiment_score, collected_at
                                          ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                                          ON DUPLICATE KEY UPDATE sentiment_score = VALUES(sentiment_score)
                                      """, (
                                          article["title"][:500],
                                          article["content"][:2000],
                                          article["url"],
                                          article["source"],
                                          article["published_at"],
                                          article["sentiment_score"]
                                      ))
                                      stored += 1
                                  except Exception as e:
                                      logger.error(f"Error storing article: {e}")
                                      continue
                                      
                              conn.commit()
                              
                      except Exception as e:
                          logger.error(f"Database error: {e}")
                          
                      return stored
                      
                  def run_collection_cycle(self):
                      logger.info("Starting crypto news collection cycle...")
                      
                      total_collected = 0
                      total_stored = 0
                      
                      for feed_url in self.rss_feeds:
                          try:
                              articles = self.fetch_rss_articles(feed_url)
                              total_collected += len(articles)
                              
                              if articles:
                                  stored = self.store_articles(articles)
                                  total_stored += stored
                                  logger.info(f"✅ {feed_url}: {len(articles)} collected, {stored} stored")
                              
                              time.sleep(2)  # Rate limiting
                              
                          except Exception as e:
                              logger.error(f"Error processing {feed_url}: {e}")
                              continue
                              
                      logger.info(f"News collection completed: {total_collected} collected, {total_stored} stored")
                      return {"collected": total_collected, "stored": total_stored}
              
              if __name__ == "__main__":
                  collector = EnhancedCryptoNewsCollector()
                  while True:
                      try:
                          collector.run_collection_cycle()
                          time.sleep(900)  # 15 minutes
                      except KeyboardInterrupt:
                          break
                      except Exception as e:
                          logger.error(f"Collection error: {e}")
                          time.sleep(300)
              PYEOF
              
              python /app/enhanced_crypto_news_collector.py
          env:
            - name: MYSQL_HOST
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_HOST
            - name: MYSQL_PORT
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PORT
            - name: MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PASSWORD
            - name: MYSQL_DATABASE
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_DATABASE
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "250m"
EOF

echo "📦 Deploying enhanced macro indicators collector..."
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-macro-indicators
  namespace: crypto-data-collection
  labels:
    app: enhanced-macro-indicators
    component: data-collection
    version: enhanced
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enhanced-macro-indicators
  template:
    metadata:
      labels:
        app: enhanced-macro-indicators
        component: data-collection
        version: enhanced
    spec:
      nodeSelector:
        node-type: data-collection
      tolerations:
        - key: "data-platform"
          operator: "Equal"
          value: "true"
          effect: "NoSchedule"
      containers:
        - name: enhanced-macro-indicators
          image: python:3.11-slim
          command: ["/bin/bash", "-c"]
          args:
            - |
              pip install mysql-connector-python requests
              
              cat > /app/enhanced_macro_collector.py << 'PYEOF'
              #!/usr/bin/env python3
              import os, logging, time, requests, mysql.connector
              from datetime import datetime, date, timedelta
              from typing import List, Dict, Optional
              
              logging.basicConfig(level=logging.INFO)
              logger = logging.getLogger(__name__)
              
              class EnhancedMacroCollector:
                  def __init__(self):
                      self.db_config = {
                          "host": os.getenv("MYSQL_HOST", "host.docker.internal"),
                          "port": int(os.getenv("MYSQL_PORT", "3306")),
                          "user": os.getenv("MYSQL_USER", "news_collector"),
                          "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
                          "database": os.getenv("MYSQL_DATABASE", "crypto_prices")
                      }
                      
                      self.fred_api_key = "35478996c5e061d0fc99fc73f5ce348d"
                      self.fred_base_url = "https://api.stlouisfed.org/fred"
                      
                      self.indicators = {
                          "10Y_TREASURY": "DGS10",
                          "2Y_TREASURY": "DGS2", 
                          "USD_JPY": "DEXJPUS",
                          "USD_EUR": "DEXUSEU",
                          "VIX": "VIXCLS",
                          "UNEMPLOYMENT_RATE": "UNRATE",
                          "CPI_INFLATION": "CPIAUCSL",
                          "FEDERAL_FUNDS_RATE": "FEDFUNDS"
                      }
                      
                  def get_db_connection(self):
                      return mysql.connector.connect(**self.db_config)
                      
                  def fetch_fred_data(self, indicator_name: str, series_id: str) -> Optional[Dict]:
                      try:
                          params = {
                              "series_id": series_id,
                              "api_key": self.fred_api_key,
                              "file_type": "json",
                              "limit": 1,
                              "sort_order": "desc"
                          }
                          
                          url = f"{self.fred_base_url}/series/observations"
                          response = requests.get(url, params=params, timeout=30)
                          response.raise_for_status()
                          
                          data = response.json()
                          observations = data.get("observations", [])
                          
                          if observations:
                              obs = observations[0]
                              value = obs.get("value")
                              
                              if value != "." and value is not None:
                                  return {
                                      "indicator_name": indicator_name,
                                      "value": float(value),
                                      "date": datetime.strptime(obs.get("date"), "%Y-%m-%d").date(),
                                      "series_id": series_id
                                  }
                                  
                          return None
                          
                      except Exception as e:
                          logger.error(f"Error fetching {indicator_name}: {e}")
                          return None
                          
                  def store_indicator_data(self, data: Dict) -> bool:
                      try:
                          with self.get_db_connection() as conn:
                              cursor = conn.cursor()
                              
                              cursor.execute("""
                                  INSERT INTO macro_indicators (
                                      indicator_name, indicator_date, value, 
                                      fred_series_id, data_source, collected_at
                                  ) VALUES (
                                      %s, %s, %s, %s, %s, NOW()
                                  ) ON DUPLICATE KEY UPDATE
                                      value = VALUES(value),
                                      collected_at = NOW()
                              """, (
                                  data["indicator_name"],
                                  data["date"],
                                  data["value"],
                                  data["series_id"],
                                  "FRED_API"
                              ))
                              
                              conn.commit()
                              return True
                              
                      except Exception as e:
                          logger.error(f"Error storing indicator data: {e}")
                          return False
                          
                  def run_collection_cycle(self):
                      logger.info("Starting macro indicators collection cycle...")
                      
                      collected = 0
                      stored = 0
                      
                      for indicator_name, series_id in self.indicators.items():
                          try:
                              data = self.fetch_fred_data(indicator_name, series_id)
                              
                              if data:
                                  collected += 1
                                  if self.store_indicator_data(data):
                                      stored += 1
                                      logger.info(f"✅ {indicator_name}: {data['value']} on {data['date']}")
                                  
                              time.sleep(1)
                              
                          except Exception as e:
                              logger.error(f"Error processing {indicator_name}: {e}")
                              continue
                              
                      logger.info(f"Collection completed: {collected} collected, {stored} stored")
                      return {"collected": collected, "stored": stored}
              
              if __name__ == "__main__":
                  collector = EnhancedMacroCollector()
                  
                  while True:
                      try:
                          collector.run_collection_cycle()
                          time.sleep(3600)  # 1 hour intervals
                      except KeyboardInterrupt:
                          break
                      except Exception as e:
                          logger.error(f"Collection error: {e}")
                          time.sleep(600)
              PYEOF
              
              python /app/enhanced_macro_collector.py
          env:
            - name: MYSQL_HOST
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_HOST
            - name: MYSQL_PORT
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PORT
            - name: MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PASSWORD
            - name: MYSQL_DATABASE
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_DATABASE
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "250m"
EOF

echo "📦 Deploying enhanced onchain data collector..."
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-onchain-data
  namespace: crypto-data-collection
  labels:
    app: enhanced-onchain-data
    component: data-collection
    version: enhanced
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enhanced-onchain-data
  template:
    metadata:
      labels:
        app: enhanced-onchain-data
        component: data-collection
        version: enhanced
    spec:
      nodeSelector:
        node-type: data-collection
      tolerations:
        - key: "data-platform"
          operator: "Equal"
          value: "true"
          effect: "NoSchedule"
      containers:
        - name: enhanced-onchain-data
          image: python:3.11-slim
          command: ["/bin/bash", "-c"]
          args:
            - |
              pip install mysql-connector-python requests
              
              cat > /app/enhanced_onchain_collector.py << 'PYEOF'
              #!/usr/bin/env python3
              import os, logging, time, requests, mysql.connector
              from datetime import datetime, timedelta
              from typing import List, Dict, Optional
              
              logging.basicConfig(level=logging.INFO)
              logger = logging.getLogger(__name__)
              
              class EnhancedOnChainCollector:
                  def __init__(self):
                      self.db_config = {
                          "host": os.getenv("MYSQL_HOST", "host.docker.internal"),
                          "port": int(os.getenv("MYSQL_PORT", "3306")),
                          "user": os.getenv("MYSQL_USER", "news_collector"),
                          "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
                          "database": os.getenv("MYSQL_DATABASE", "crypto_prices")
                      }
                      
                      self.blockchain_apis = {
                          "bitcoin": {
                              "base_url": "https://blockstream.info/api",
                              "endpoints": {
                                  "stats": "/stats",
                                  "mempool": "/mempool"
                              }
                          }
                      }
                      
                  def get_db_connection(self):
                      return mysql.connector.connect(**self.db_config)
                      
                  def fetch_bitcoin_onchain_data(self) -> Optional[Dict]:
                      try:
                          stats_url = f"{self.blockchain_apis['bitcoin']['base_url']}/stats"
                          stats_response = requests.get(stats_url, timeout=30)
                          stats_response.raise_for_status()
                          stats = stats_response.json()
                          
                          mempool_url = f"{self.blockchain_apis['bitcoin']['base_url']}/mempool"
                          mempool_response = requests.get(mempool_url, timeout=30)
                          mempool_response.raise_for_status()
                          mempool = mempool_response.json()
                          
                          return {
                              "symbol": "BTC",
                              "blockchain": "bitcoin",
                              "mempool_size": mempool.get("count", 0),
                              "mempool_vsize": mempool.get("vsize", 0),
                              "total_fees": mempool.get("total_fee", 0),
                              "metric_date": datetime.now().date()
                          }
                          
                      except Exception as e:
                          logger.error(f"Error fetching Bitcoin data: {e}")
                          return None
                          
                  def store_onchain_data(self, data: Dict) -> bool:
                      try:
                          with self.get_db_connection() as conn:
                              cursor = conn.cursor()
                              
                              cursor.execute("""
                                  INSERT INTO onchain_data (
                                      symbol, blockchain, mempool_size, mempool_vsize, 
                                      total_fees, metric_date, collected_at
                                  ) VALUES (
                                      %s, %s, %s, %s, %s, %s, NOW()
                                  ) ON DUPLICATE KEY UPDATE
                                      mempool_size = VALUES(mempool_size),
                                      mempool_vsize = VALUES(mempool_vsize),
                                      total_fees = VALUES(total_fees),
                                      collected_at = NOW()
                              """, (
                                  data["symbol"],
                                  data["blockchain"],
                                  data["mempool_size"],
                                  data["mempool_vsize"],
                                  data["total_fees"],
                                  data["metric_date"]
                              ))
                              
                              conn.commit()
                              return True
                              
                      except Exception as e:
                          logger.error(f"Error storing onchain data: {e}")
                          return False
                          
                  def run_collection_cycle(self):
                      logger.info("Starting onchain data collection cycle...")
                      
                      collected = 0
                      stored = 0
                      
                      try:
                          btc_data = self.fetch_bitcoin_onchain_data()
                          if btc_data:
                              collected += 1
                              if self.store_onchain_data(btc_data):
                                  stored += 1
                                  logger.info(f"✅ BTC onchain: mempool_size={btc_data.get('mempool_size')}")
                          
                      except Exception as e:
                          logger.error(f"Error processing Bitcoin data: {e}")
                          
                      logger.info(f"OnChain collection completed: {collected} collected, {stored} stored")
                      return {"collected": collected, "stored": stored}
              
              if __name__ == "__main__":
                  collector = EnhancedOnChainCollector()
                  
                  while True:
                      try:
                          collector.run_collection_cycle()
                          time.sleep(1800)  # 30 minutes
                      except KeyboardInterrupt:
                          break
                      except Exception as e:
                          logger.error(f"Collection error: {e}")
                          time.sleep(600)
              PYEOF
              
              python /app/enhanced_onchain_collector.py
          env:
            - name: MYSQL_HOST
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_HOST
            - name: MYSQL_PORT
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PORT
            - name: MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_PASSWORD
            - name: MYSQL_DATABASE
              valueFrom:
                configMapKeyRef:
                  name: centralized-db-config
                  key: MYSQL_DATABASE
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "250m"
EOF

echo "✅ Enhanced collectors deployment complete!"
echo "📊 Checking deployment status..."
kubectl get deployments -n crypto-data-collection | grep enhanced