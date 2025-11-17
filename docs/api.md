# Data Collection System API Documentation

This document provides comprehensive API documentation for the crypto data collection system, including authentication, endpoints, examples, and integration patterns.

## 🌐 **API Overview**

### **Base URLs**
- **Production**: `https://data-api.crypto-trading.com`
- **Staging**: `https://data-api-staging.crypto-trading.com`
- **Development**: `http://localhost:8000`
- **Kubernetes Internal**: `http://data-api-gateway.crypto-collectors.svc.cluster.local:8000`

### **API Versions**
- **Current Version**: v1
- **Supported Versions**: v1
- **Version Header**: `Accept: application/vnd.crypto-data.v1+json`

### **Content Types**
- **Request**: `application/json`
- **Response**: `application/json`
- **Streaming**: `text/event-stream` (Server-Sent Events)
- **WebSocket**: `application/json` over WebSocket

## 🔐 **Authentication**

### **API Key Authentication**
All API endpoints require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://data-api.crypto-trading.com/api/v1/prices/current/bitcoin
```

### **API Key Management**
```python
# Python example
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.crypto-data.v1+json'
}

response = requests.get(
    'https://data-api.crypto-trading.com/api/v1/health',
    headers=headers
)
```

### **Rate Limiting**
- **Default Limit**: 1000 requests/hour
- **Premium Tier**: 10000 requests/hour
- **Burst Limit**: 100 requests/minute
- **Headers**: Rate limit info included in response headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 📊 **Core Endpoints**

### **System Health & Status**

#### `GET /health`
System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "services": {
    "collectors": {
      "crypto-prices": "healthy",
      "crypto-news": "healthy",
      "technical-indicators": "healthy"
    },
    "processors": {
      "sentiment-analysis": "healthy",
      "ml-features": "healthy"
    },
    "database": {
      "mysql": "healthy",
      "redis": "healthy"
    }
  },
  "uptime_seconds": 86400
}
```

#### `GET /metrics`
Prometheus metrics endpoint for monitoring.

**Response Format:** Prometheus text format
```
# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total{method="GET",endpoint="/api/v1/prices",status="200"} 1547

# HELP request_duration_seconds Request duration in seconds
# TYPE request_duration_seconds histogram
request_duration_seconds_bucket{le="0.1"} 1000
request_duration_seconds_bucket{le="0.5"} 1500
```

### **Cryptocurrency Prices**

#### `GET /api/v1/prices/current/{symbol}`
Get current price data for a specific cryptocurrency.

**Parameters:**
- `symbol` (string, required): Cryptocurrency symbol (e.g., "bitcoin", "ethereum")

**Query Parameters:**
- `vs_currencies` (string, optional): Comma-separated list of fiat currencies. Default: "usd"
- `include_24hr_change` (boolean, optional): Include 24-hour price change. Default: true
- `include_market_cap` (boolean, optional): Include market capitalization. Default: true

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://data-api.crypto-trading.com/api/v1/prices/current/bitcoin?vs_currencies=usd,eur&include_24hr_change=true"
```

**Response:**
```json
{
  "symbol": "bitcoin",
  "name": "Bitcoin",
  "current_price": {
    "usd": 45000.50,
    "eur": 39500.25
  },
  "market_cap": {
    "usd": 850000000000,
    "eur": 745000000000
  },
  "volume_24h": {
    "usd": 25000000000,
    "eur": 21900000000
  },
  "price_change_24h": {
    "usd": 1250.75,
    "eur": 1095.50
  },
  "price_change_percentage_24h": {
    "usd": 2.86,
    "eur": 2.86
  },
  "last_updated": "2025-01-15T10:30:00.000Z",
  "data_source": "coingecko_premium"
}
```

#### `GET /api/v1/prices/historical/{symbol}`
Get historical price data for a specific cryptocurrency.

**Parameters:**
- `symbol` (string, required): Cryptocurrency symbol

**Query Parameters:**
- `days` (integer, optional): Number of days of historical data. Default: 7, Max: 365
- `interval` (string, optional): Data interval. Options: "1h", "4h", "1d". Default: "1d"
- `vs_currency` (string, optional): Fiat currency. Default: "usd"

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://data-api.crypto-trading.com/api/v1/prices/historical/bitcoin?days=30&interval=1d"
```

**Response:**
```json
{
  "symbol": "bitcoin",
  "vs_currency": "usd",
  "interval": "1d",
  "data": [
    {
      "timestamp": "2024-12-16T00:00:00.000Z",
      "open": 44000.00,
      "high": 45500.00,
      "low": 43500.00,
      "close": 45000.00,
      "volume": 24000000000
    },
    {
      "timestamp": "2024-12-17T00:00:00.000Z",
      "open": 45000.00,
      "high": 46200.00,
      "low": 44800.00,
      "close": 46000.00,
      "volume": 26000000000
    }
  ],
  "total_points": 30,
  "data_source": "coingecko_premium"
}
```

### **Sentiment Analysis**

#### `GET /api/v1/sentiment/crypto/{symbol}`
Get sentiment analysis for a specific cryptocurrency.

**Parameters:**
- `symbol` (string, required): Cryptocurrency symbol

**Query Parameters:**
- `sources` (string, optional): Comma-separated list of sources. Options: "news", "reddit", "twitter". Default: "all"
- `timeframe` (string, optional): Time period for analysis. Options: "1h", "4h", "24h", "7d". Default: "24h"
- `include_breakdown` (boolean, optional): Include sentiment breakdown by source. Default: false

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://data-api.crypto-trading.com/api/v1/sentiment/crypto/bitcoin?timeframe=24h&include_breakdown=true"
```

**Response:**
```json
{
  "symbol": "bitcoin",
  "overall_sentiment": {
    "score": 0.65,
    "label": "bullish",
    "confidence": 0.82
  },
  "timeframe": "24h",
  "sample_size": 1547,
  "breakdown": {
    "news": {
      "score": 0.71,
      "label": "bullish",
      "articles_analyzed": 89,
      "model": "cryptobert"
    },
    "reddit": {
      "score": 0.58,
      "label": "neutral_bullish",
      "posts_analyzed": 1205,
      "subreddits": ["cryptocurrency", "bitcoin", "investing"]
    },
    "twitter": {
      "score": 0.67,
      "label": "bullish",
      "tweets_analyzed": 253,
      "verified_accounts_weight": 0.35
    }
  },
  "sentiment_history_24h": [
    {
      "timestamp": "2025-01-15T09:00:00.000Z",
      "score": 0.62
    },
    {
      "timestamp": "2025-01-15T10:00:00.000Z",
      "score": 0.65
    }
  ],
  "last_updated": "2025-01-15T10:30:00.000Z"
}
```

### **Technical Analysis**

#### `GET /api/v1/technical/{symbol}`
Get technical indicators for a specific cryptocurrency.

**Parameters:**
- `symbol` (string, required): Cryptocurrency symbol

**Query Parameters:**
- `indicators` (string, optional): Comma-separated list of indicators. Options: "rsi", "macd", "bollinger", "sma", "ema". Default: "all"
- `timeframe` (string, optional): Chart timeframe. Options: "1h", "4h", "1d". Default: "1d"
- `periods` (integer, optional): Number of periods for calculation. Default: 14

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://data-api.crypto-trading.com/api/v1/technical/bitcoin?indicators=rsi,macd&timeframe=4h"
```

**Response:**
```json
{
  "symbol": "bitcoin",
  "timeframe": "4h",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "indicators": {
    "rsi": {
      "value": 62.5,
      "signal": "neutral",
      "overbought_threshold": 70,
      "oversold_threshold": 30,
      "period": 14
    },
    "macd": {
      "macd_line": 450.25,
      "signal_line": 425.80,
      "histogram": 24.45,
      "signal": "bullish",
      "crossover": "bullish_crossover"
    },
    "bollinger_bands": {
      "upper_band": 46500.00,
      "middle_band": 45000.00,
      "lower_band": 43500.00,
      "current_position": "middle",
      "bandwidth": 6.67,
      "squeeze": false
    },
    "moving_averages": {
      "sma_20": 44800.50,
      "sma_50": 44200.25,
      "ema_20": 44950.75,
      "ema_50": 44350.00,
      "price_vs_sma20": "above",
      "price_vs_sma50": "above"
    }
  },
  "overall_signal": {
    "direction": "bullish",
    "strength": "moderate",
    "confidence": 0.72
  }
}
```

### **ML Features**

#### `GET /api/v1/ml-features/{symbol}`
Get machine learning features for a specific cryptocurrency.

**Parameters:**
- `symbol` (string, required): Cryptocurrency symbol

**Query Parameters:**
- `feature_groups` (string, optional): Comma-separated groups. Options: "price", "technical", "sentiment", "onchain", "macro". Default: "all"
- `latest_only` (boolean, optional): Return only latest feature set. Default: true
- `format` (string, optional): Response format. Options: "structured", "flat", "array". Default: "structured"

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://data-api.crypto-trading.com/api/v1/ml-features/bitcoin?feature_groups=price,technical,sentiment"
```

**Response:**
```json
{
  "symbol": "bitcoin",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "feature_version": "2.1",
  "features": {
    "price_features": {
      "price_usd": 45000.50,
      "price_change_1h": 0.0125,
      "price_change_24h": 0.0286,
      "price_change_7d": 0.0845,
      "price_volatility_24h": 0.0234,
      "volume_usd_24h": 25000000000,
      "volume_change_24h": 0.1256,
      "market_cap_usd": 850000000000,
      "market_cap_rank": 1
    },
    "technical_features": {
      "rsi_14": 62.5,
      "macd_signal": 1,
      "bb_position": 0.5,
      "sma_20_distance": 0.0045,
      "sma_50_distance": 0.0178,
      "ema_12_slope": 0.0023,
      "atr_14": 1250.75,
      "volume_sma_ratio": 1.15
    },
    "sentiment_features": {
      "news_sentiment_24h": 0.65,
      "social_sentiment_24h": 0.58,
      "sentiment_change_6h": 0.05,
      "sentiment_volatility": 0.12,
      "news_volume_24h": 89,
      "social_volume_24h": 1205,
      "fear_greed_index": 72,
      "crypto_correlation_score": 0.67
    }
  },
  "feature_count": 32,
  "data_quality_score": 0.96
}
```

## 🔄 **Real-time Data Streams**

### **WebSocket Connections**

#### Price Streams
**URL:** `wss://data-api.crypto-trading.com/ws/prices`

**Subscription Message:**
```json
{
  "action": "subscribe",
  "symbols": ["bitcoin", "ethereum", "solana"],
  "channels": ["price", "volume", "market_cap"]
}
```

**Price Update Message:**
```json
{
  "type": "price_update",
  "symbol": "bitcoin",
  "data": {
    "price_usd": 45125.75,
    "volume_24h": 25100000000,
    "market_cap": 851500000000,
    "change_24h": 2.89
  },
  "timestamp": "2025-01-15T10:30:15.000Z"
}
```

#### Sentiment Streams
**URL:** `wss://data-api.crypto-trading.com/ws/sentiment`

**Subscription Message:**
```json
{
  "action": "subscribe",
  "symbols": ["bitcoin"],
  "sources": ["news", "reddit", "twitter"]
}
```

**Sentiment Update Message:**
```json
{
  "type": "sentiment_update",
  "symbol": "bitcoin",
  "source": "news",
  "data": {
    "sentiment_score": 0.72,
    "article_title": "Bitcoin Adoption Reaches New Milestone",
    "confidence": 0.89
  },
  "timestamp": "2025-01-15T10:30:20.000Z"
}
```

### **Server-Sent Events (SSE)**

#### Real-time Price Feed
**URL:** `GET /api/v1/stream/prices`

**Query Parameters:**
- `symbols` (string, required): Comma-separated list of symbols
- `fields` (string, optional): Comma-separated list of fields. Default: "price,volume"

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Accept: text/event-stream" \
     "https://data-api.crypto-trading.com/api/v1/stream/prices?symbols=bitcoin,ethereum"
```

**SSE Response:**
```
data: {"symbol": "bitcoin", "price": 45000.50, "volume": 25000000000, "timestamp": "2025-01-15T10:30:00.000Z"}

data: {"symbol": "ethereum", "price": 2800.25, "volume": 12000000000, "timestamp": "2025-01-15T10:30:01.000Z"}

data: {"symbol": "bitcoin", "price": 45025.75, "volume": 25100000000, "timestamp": "2025-01-15T10:30:02.000Z"}
```

## ⚠️ **Error Handling**

### **Standard Error Response**
```json
{
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "The provided cryptocurrency symbol 'invalid_coin' is not supported",
    "details": {
      "supported_symbols": ["bitcoin", "ethereum", "solana", "..."]
    },
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req_12345-67890-abcdef"
  }
}
```

### **HTTP Status Codes**
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Missing or invalid API key
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### **Error Codes**
- `INVALID_API_KEY`: API key is missing or invalid
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_SYMBOL`: Cryptocurrency symbol not supported
- `INVALID_TIMEFRAME`: Timeframe parameter invalid
- `DATA_NOT_AVAILABLE`: Requested data not available
- `SERVICE_UNAVAILABLE`: External service unavailable
- `VALIDATION_ERROR`: Request validation failed

## 🔧 **SDKs & Integration Examples**

### **Python SDK Example**
```python
import asyncio
import aiohttp
from typing import Dict, List, Optional

class CryptoDataAPI:
    def __init__(self, api_key: str, base_url: str = "https://data-api.crypto-trading.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_current_price(self, symbol: str, vs_currencies: str = "usd") -> Dict:
        url = f"{self.base_url}/api/v1/prices/current/{symbol}"
        params = {"vs_currencies": vs_currencies}
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_sentiment(self, symbol: str, timeframe: str = "24h") -> Dict:
        url = f"{self.base_url}/api/v1/sentiment/crypto/{symbol}"
        params = {"timeframe": timeframe, "include_breakdown": True}
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_ml_features(self, symbol: str, feature_groups: str = "all") -> Dict:
        url = f"{self.base_url}/api/v1/ml-features/{symbol}"
        params = {"feature_groups": feature_groups}
        
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

# Usage example
async def main():
    async with CryptoDataAPI("your_api_key") as api:
        # Get current Bitcoin price
        price_data = await api.get_current_price("bitcoin")
        print(f"Bitcoin price: ${price_data['current_price']['usd']}")
        
        # Get sentiment analysis
        sentiment_data = await api.get_sentiment("bitcoin")
        print(f"Bitcoin sentiment: {sentiment_data['overall_sentiment']['score']}")
        
        # Get ML features
        ml_features = await api.get_ml_features("bitcoin", "price,technical")
        print(f"ML features: {len(ml_features['features']['price_features'])} price features")

if __name__ == "__main__":
    asyncio.run(main())
```

### **JavaScript/Node.js SDK Example**
```javascript
const axios = require('axios');
const WebSocket = require('ws');

class CryptoDataAPI {
    constructor(apiKey, baseURL = 'https://data-api.crypto-trading.com') {
        this.apiKey = apiKey;
        this.baseURL = baseURL;
        this.axios = axios.create({
            baseURL: this.baseURL,
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            }
        });
    }
    
    async getCurrentPrice(symbol, vsCurrencies = 'usd') {
        const response = await this.axios.get(`/api/v1/prices/current/${symbol}`, {
            params: { vs_currencies: vsCurrencies }
        });
        return response.data;
    }
    
    async getSentiment(symbol, timeframe = '24h') {
        const response = await this.axios.get(`/api/v1/sentiment/crypto/${symbol}`, {
            params: { timeframe, include_breakdown: true }
        });
        return response.data;
    }
    
    async getMLFeatures(symbol, featureGroups = 'all') {
        const response = await this.axios.get(`/api/v1/ml-features/${symbol}`, {
            params: { feature_groups: featureGroups }
        });
        return response.data;
    }
    
    // WebSocket streaming
    subscribeToPrices(symbols, onMessage, onError) {
        const ws = new WebSocket('wss://data-api.crypto-trading.com/ws/prices', {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`
            }
        });
        
        ws.on('open', () => {
            ws.send(JSON.stringify({
                action: 'subscribe',
                symbols: symbols,
                channels: ['price', 'volume']
            }));
        });
        
        ws.on('message', (data) => {
            const message = JSON.parse(data.toString());
            onMessage(message);
        });
        
        ws.on('error', onError);
        
        return ws;
    }
}

// Usage example
async function main() {
    const api = new CryptoDataAPI('your_api_key');
    
    try {
        // Get current Bitcoin price
        const priceData = await api.getCurrentPrice('bitcoin');
        console.log(`Bitcoin price: $${priceData.current_price.usd}`);
        
        // Get sentiment analysis
        const sentimentData = await api.getSentiment('bitcoin');
        console.log(`Bitcoin sentiment: ${sentimentData.overall_sentiment.score}`);
        
        // Subscribe to real-time price updates
        const ws = api.subscribeToPrices(['bitcoin', 'ethereum'], 
            (message) => {
                console.log('Price update:', message);
            },
            (error) => {
                console.error('WebSocket error:', error);
            }
        );
        
    } catch (error) {
        console.error('API error:', error.response?.data || error.message);
    }
}

main();
```

This API documentation provides comprehensive information for integrating with the crypto data collection system across various use cases and programming languages.