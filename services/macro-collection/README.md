# Macro Economic Collection Service

## Overview
Comprehensive macro economic data collector sourcing indicators from Federal Reserve Economic Data (FRED) API and financial markets.

## Data Sources
- **FRED API**: Federal Reserve Economic Data
- **Yahoo Finance**: Market indices and yields
- **Economic Indicators**: Real-time macro metrics

## Indicators Collected
### Federal Reserve Data
- Federal Funds Rate
- GDP Growth Rate
- Unemployment Rate
- Inflation (CPI, PCE)
- Money Supply (M1, M2)

### Market Data  
- Treasury Yields (2Y, 5Y, 10Y, 30Y)
- US Dollar Index (DXY)
- VIX Volatility Index
- S&P 500 Index

## Configuration
- **Schedule**: Hourly collection
- **Port**: 8003
- **Health Check**: `/health` endpoint
- **Database**: Stores to `macro_indicators` table

## Deployment
Deployed via Kubernetes in `crypto-data-collection` namespace:
```bash
kubectl get pods -n crypto-data-collection | grep macro-collector
```

## API Requirements
- FRED API key required for economic data
- Rate limits: 120 requests per minute
- Automatic retry with exponential backoff

## Data Processing
- Real-time indicator calculations
- Historical data validation
- Economic surprise index computation