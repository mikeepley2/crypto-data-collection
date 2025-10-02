# DATA COLLECTION SYSTEM - TABLE REFERENCE GUIDE

## 📊 **DATABASE STRUCTURE REFERENCE**

### **CRYPTO_PRICES Database Tables:**
- `price_data_real` - Real-time cryptocurrency prices (PRIMARY price data)
- `technical_indicators` - Technical analysis indicators (SMA, EMA, MACD, etc.)
- `macro_indicators` - Economic indicators (DXY, GOLD, OIL, SPX, TNX)
- `crypto_onchain_data` - Blockchain metrics and onchain data
- `ml_features_materialized` - ML features generated from price data
- `crypto_assets` - Symbol definitions and metadata

### **CRYPTO_NEWS Database Tables:**
- `crypto_sentiment_data` - Crypto-specific sentiment analysis
- `social_sentiment_data` - Social media sentiment (Reddit, Twitter)
- `stock_sentiment_data` - Stock market sentiment analysis
- `stock_market_news_data` - Stock market news articles
- `crypto_news_data` - Cryptocurrency news articles
- `macro_economic_data` - Economic news and data (STALE TABLE)
- `technical_indicators` - STALE TABLE (use crypto_prices.technical_indicators instead)

## 🔍 **DATA COLLECTION STATUS PATTERNS:**

### **Working Collectors:**
1. **Enhanced-Crypto-Prices** → `crypto_prices.price_data_real`
2. **Materialized-Updater** → `crypto_prices.ml_features_materialized`
3. **Onchain Data Collector** → `crypto_prices.crypto_onchain_data`
4. **Technical Indicators** → `crypto_prices.technical_indicators` (daily updates)
5. **Macro Indicators** → `crypto_prices.macro_indicators` (daily updates)

### **Missing/Broken Collectors:**
1. **Social Sentiment** → `crypto_news.social_sentiment_data` (stale since 2025-09-04)
2. **Stock Sentiment** → `crypto_news.stock_sentiment_data` (stale since 2025-09-04)
3. **Crypto Sentiment** → `crypto_news.crypto_sentiment_data` (minimal data)

## ⚠️ **IMPORTANT NOTES:**
- Always check `crypto_prices` database first for core data (prices, technical, macro)
- Sentiment data is primarily in `crypto_news` database
- Some tables in `crypto_news` are stale duplicates (e.g., technical_indicators, macro_economic_data)
- Fresh data should be < 24-48 hours old for most active collectors