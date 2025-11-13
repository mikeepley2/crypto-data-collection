#!/bin/bash

echo "🔧 Fixing Enhanced Collectors - Creating App Directory First..."

kubectl delete deployment enhanced-crypto-news -n crypto-data-collection --ignore-not-found
kubectl delete deployment enhanced-technical-calculator -n crypto-data-collection --ignore-not-found

echo "📦 Deploying fixed enhanced crypto news collector..."
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-crypto-news
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
              pip install mysql-connector-python requests feedparser beautifulsoup4 python-dateutil
              
              mkdir -p /app
              cat > /app/enhanced_crypto_news_collector.py << 'PYEOF'
              #!/usr/bin/env python3
              import os, logging, time, requests, mysql.connector, feedparser
              from datetime import datetime, timedelta
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
                              
                              time.sleep(2)
                              
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
              
              echo "🚀 Enhanced Crypto News Collector starting..."
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
              memory: "128Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "150m"
EOF

echo "📦 Deploying fixed enhanced technical calculator..."
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-technical-calculator
  namespace: crypto-data-collection
  labels:
    app: enhanced-technical-calculator
    component: data-collection
    version: enhanced
spec:
  replicas: 1
  selector:
    matchLabels:
      app: enhanced-technical-calculator
  template:
    metadata:
      labels:
        app: enhanced-technical-calculator
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
        - name: enhanced-technical-calculator
          image: python:3.11-slim
          command: ["/bin/bash", "-c"]
          args:
            - |
              pip install mysql-connector-python requests numpy pandas
              
              mkdir -p /app
              cat > /app/enhanced_technical_calculator.py << 'PYEOF'
              #!/usr/bin/env python3
              import os, logging, time, mysql.connector, numpy as np, pandas as pd
              from datetime import datetime, timedelta
              from typing import List, Dict, Optional, Tuple
              
              logging.basicConfig(level=logging.INFO)
              logger = logging.getLogger(__name__)
              
              class EnhancedTechnicalCalculator:
                  def __init__(self):
                      self.db_config = {
                          "host": os.getenv("MYSQL_HOST", "host.docker.internal"),
                          "port": int(os.getenv("MYSQL_PORT", "3306")),
                          "user": os.getenv("MYSQL_USER", "news_collector"),
                          "password": os.getenv("MYSQL_PASSWORD", "99Rules!"),
                          "database": os.getenv("MYSQL_DATABASE", "crypto_prices")
                      }
                      
                  def get_db_connection(self):
                      return mysql.connector.connect(**self.db_config)
                      
                  def get_active_symbols(self) -> List[str]:
                      try:
                          with self.get_db_connection() as conn:
                              cursor = conn.cursor()
                              cursor.execute("""
                                  SELECT DISTINCT symbol FROM crypto_assets 
                                  WHERE is_active = 1 
                                  ORDER BY market_cap_rank ASC, symbol ASC
                                  LIMIT 50
                              """)
                              return [row[0] for row in cursor.fetchall()]
                      except Exception as e:
                          logger.error(f"Error fetching symbols: {e}")
                          return ["bitcoin", "ethereum", "cardano", "polkadot", "chainlink"]
                          
                  def get_price_data(self, symbol: str, days: int = 50) -> pd.DataFrame:
                      try:
                          with self.get_db_connection() as conn:
                              query = """
                                  SELECT timestamp, price as close
                                  FROM crypto_prices 
                                  WHERE symbol = %s 
                                    AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                                  ORDER BY timestamp ASC
                              """
                              
                              df = pd.read_sql(query, conn, params=(symbol, days))
                              
                              if len(df) > 0:
                                  df['timestamp'] = pd.to_datetime(df['timestamp'])
                                  df.set_index('timestamp', inplace=True)
                                  return df
                                  
                          return pd.DataFrame()
                          
                      except Exception as e:
                          logger.error(f"Error fetching price data for {symbol}: {e}")
                          return pd.DataFrame()
                          
                  def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
                      sma = prices.rolling(window=window).mean()
                      std = prices.rolling(window=window).std()
                      
                      upper_band = sma + (std * std_dev)
                      lower_band = sma - (std * std_dev)
                      
                      return upper_band, sma, lower_band
                      
                  def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
                      delta = prices.diff()
                      gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
                      loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
                      
                      rs = gain / loss
                      rsi = 100 - (100 / (1 + rs))
                      
                      return rsi
                      
                  def calculate_technical_indicators(self, symbol: str) -> Optional[Dict]:
                      try:
                          df = self.get_price_data(symbol)
                          
                          if df.empty or len(df) < 26:
                              return None
                              
                          prices = df['close']
                          latest_price = prices.iloc[-1]
                          latest_timestamp = df.index[-1]
                          
                          # Bollinger Bands
                          bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
                          
                          # RSI
                          rsi = self.calculate_rsi(prices)
                          
                          # Moving Averages
                          sma_20 = prices.rolling(20).mean()
                          ema_20 = prices.ewm(span=20).mean()
                          
                          return {
                              "symbol": symbol,
                              "timestamp": latest_timestamp,
                              "price": latest_price,
                              "sma_20": sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else None,
                              "ema_20": ema_20.iloc[-1] if not pd.isna(ema_20.iloc[-1]) else None,
                              "bollinger_upper": bb_upper.iloc[-1] if not pd.isna(bb_upper.iloc[-1]) else None,
                              "bollinger_middle": bb_middle.iloc[-1] if not pd.isna(bb_middle.iloc[-1]) else None,
                              "bollinger_lower": bb_lower.iloc[-1] if not pd.isna(bb_lower.iloc[-1]) else None,
                              "rsi": rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None
                          }
                          
                      except Exception as e:
                          logger.error(f"Error calculating indicators for {symbol}: {e}")
                          return None
                          
                  def store_technical_indicators(self, data: Dict) -> bool:
                      try:
                          with self.get_db_connection() as conn:
                              cursor = conn.cursor()
                              
                              cursor.execute("""
                                  INSERT INTO technical_indicators (
                                      symbol, timestamp, price, sma_20, ema_20,
                                      bollinger_upper, bollinger_middle, bollinger_lower,
                                      rsi, calculated_at
                                  ) VALUES (
                                      %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                                  ) ON DUPLICATE KEY UPDATE
                                      price = VALUES(price),
                                      sma_20 = VALUES(sma_20),
                                      ema_20 = VALUES(ema_20),
                                      bollinger_upper = VALUES(bollinger_upper),
                                      bollinger_middle = VALUES(bollinger_middle),
                                      bollinger_lower = VALUES(bollinger_lower),
                                      rsi = VALUES(rsi),
                                      calculated_at = NOW()
                              """, (
                                  data["symbol"],
                                  data["timestamp"],
                                  data["price"],
                                  data.get("sma_20"),
                                  data.get("ema_20"),
                                  data.get("bollinger_upper"),
                                  data.get("bollinger_middle"),
                                  data.get("bollinger_lower"),
                                  data.get("rsi")
                              ))
                              
                              conn.commit()
                              return True
                              
                      except Exception as e:
                          logger.error(f"Error storing technical data: {e}")
                          return False
                          
                  def run_calculation_cycle(self):
                      logger.info("Starting technical indicators calculation cycle...")
                      
                      symbols = self.get_active_symbols()
                      calculated = 0
                      stored = 0
                      
                      for symbol in symbols:
                          try:
                              data = self.calculate_technical_indicators(symbol)
                              
                              if data:
                                  calculated += 1
                                  if self.store_technical_indicators(data):
                                      stored += 1
                                      logger.info(f"✅ {symbol}: RSI={data.get('rsi', 'N/A'):.2f}" if data.get('rsi') else f"✅ {symbol}: Calculated")
                                  
                              time.sleep(0.5)
                              
                          except Exception as e:
                              logger.error(f"Error processing {symbol}: {e}")
                              continue
                              
                      logger.info(f"Technical calculation completed: {calculated} calculated, {stored} stored")
                      return {"calculated": calculated, "stored": stored}
              
              if __name__ == "__main__":
                  calculator = EnhancedTechnicalCalculator()
                  
                  while True:
                      try:
                          calculator.run_calculation_cycle()
                          time.sleep(600)  # 10 minutes
                      except KeyboardInterrupt:
                          break
                      except Exception as e:
                          logger.error(f"Calculation error: {e}")
                          time.sleep(300)
              PYEOF
              
              echo "🚀 Enhanced Technical Calculator starting..."
              python /app/enhanced_technical_calculator.py
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
              memory: "128Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "150m"
EOF

echo "✅ Fixed enhanced collectors deployed!"
echo "📊 Checking deployment status..."
kubectl get deployments -n crypto-data-collection | grep enhanced