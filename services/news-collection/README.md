# News Collection Service

## Overview
Cryptocurrency news aggregation and sentiment analysis service processing articles from 26+ RSS feeds and news sources.

## Data Sources
### RSS Feeds (26 sources)
- CoinDesk, CoinTelegraph, CryptoNews
- Bitcoin Magazine, Decrypt, The Block
- Benzinga Crypto, U.Today, NewsBTC
- CryptoSlate, AMBCrypto, CryptoPotato
- And 14 additional crypto news sources

### News APIs
- Cryptocurrency-specific news aggregators
- Financial news services with crypto coverage

## Sentiment Analysis
### ML Models Used
- **CryptoBERT**: Crypto-specific BERT model
- **VADER**: Valence Aware Dictionary and sEntiment Reasoner  
- **TextBlob**: Pattern-based sentiment analysis
- **Crypto Keywords**: Domain-specific sentiment scoring

### Analysis Types
- **General Crypto Sentiment**: Market-wide news sentiment
- **Symbol-Specific Sentiment**: Asset-specific news analysis
- **Fear & Greed Integration**: Market psychology indicators

## Configuration
- **Collection Interval**: Every 15 minutes
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Database**: Stores to `crypto_news` and `sentiment_aggregation` tables

## Data Processing
- Duplicate article detection (24-hour TTL)
- Content cleaning and preprocessing
- Multi-model sentiment scoring
- Temporal sentiment aggregation

## Deployment
```bash
kubectl get pods -n crypto-data-collection | grep crypto-news
```

## Quality Controls
- Source reliability scoring
- Content validation
- Sentiment score normalization
- Real-time processing alerts