# Derivatives Collection Service

## Overview
Multi-exchange derivatives data collector providing real-time funding rates, open interest, options data, and liquidation metrics from 5 major cryptocurrency exchanges.

## Supported Exchanges
- **Binance**: Perpetual futures funding rates, open interest
- **Bybit**: Derivatives metrics, liquidation data
- **OKX**: Multi-asset derivatives coverage
- **Deribit**: Options data, volatility metrics  
- **KuCoin**: Funding rates, futures data

## Data Collected
- Funding rates (all supported assets)
- Open interest (perpetual futures)
- Options put/call ratios
- Liquidation volumes (long/short)
- Derivatives volume metrics

## Configuration
- **Schedule**: Every 5 minutes via CronJob
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Database**: Stores to `derivatives_data` table

## Deployment
Deployed via Kubernetes in `crypto-data-collection` namespace:
```bash
kubectl get pods -n crypto-data-collection | grep derivatives-collector
```

## Monitoring
- Health checks every 30 seconds
- Prometheus metrics collection
- Error handling and retry logic

## Data Quality
- Real-time validation of exchange data
- Automatic fallback between exchanges
- Duplicate detection and deduplication