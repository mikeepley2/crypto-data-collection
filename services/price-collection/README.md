# Price Collection Service

## Overview
Core cryptocurrency price collection service providing real-time pricing, market cap, volume, and fundamental market data from CoinGecko API.

## Data Collected
### Core Price Data
- **Current Price**: Real-time USD price
- **Market Cap**: Total market capitalization
- **24h Volume**: Daily trading volume
- **Price Changes**: 24h absolute and percentage changes
- **Hourly Volume**: Volume breakdown by hour

### Market Metrics
- **Market Cap Rank**: Position in market cap rankings
- **Circulating Supply**: Available token supply
- **Total Supply**: Maximum token supply
- **All-Time High/Low**: Historical price extremes

## Supported Assets
- **Bitcoin (BTC)**: Primary cryptocurrency
- **Ethereum (ETH)**: Smart contract platform
- **Major Altcoins**: Top 100 by market cap
- **DeFi Tokens**: Decentralized finance assets
- **Layer 1/2 Tokens**: Blockchain infrastructure

## Configuration
- **Collection Interval**: Every 5 minutes
- **Port**: 8000
- **Data Source**: CoinGecko API
- **Database**: Stores to `crypto_prices` table

## API Integration
### CoinGecko API
- **Rate Limits**: 100 calls/minute (free tier)
- **Pro Features**: Higher limits, additional data
- **Endpoints Used**: `/simple/price`, `/coins/markets`

### Data Quality
- Real-time price validation
- Market cap verification
- Volume anomaly detection
- Cross-reference with multiple sources

## Deployment
```bash
kubectl get pods -n crypto-data-collection | grep crypto-prices
```

## Features
- Historical price tracking
- Real-time market updates
- Multi-currency support (USD, BTC, ETH)
- Market trend analysis