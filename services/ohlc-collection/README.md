# OHLC Collection Service

## Overview
Open-High-Low-Close price data collection service providing comprehensive historical and real-time price action data for cryptocurrency assets.

## Data Collected
### OHLC Metrics
- **Open**: Opening price for timeframe
- **High**: Highest price within timeframe  
- **Low**: Lowest price within timeframe
- **Close**: Closing price for timeframe
- **Volume**: Trading volume for timeframe

### Timeframes Supported
- **1 minute**: High-frequency trading data
- **5 minutes**: Short-term analysis
- **15 minutes**: Intraday patterns
- **1 hour**: Standard analysis timeframe
- **4 hours**: Medium-term trends
- **1 day**: Daily price action

## Data Sources
- **Primary**: CoinGecko API
- **Secondary**: Direct exchange APIs
- **Backup**: Multiple data providers for redundancy

## Configuration
- **Collection Interval**: Every 5 minutes
- **Port**: 8000
- **Health Check**: `/health` endpoint
- **Database**: Stores to `ohlc_data` table

## Price Action Analysis
### Technical Patterns
- Candlestick pattern recognition
- Gap analysis (weekend/maintenance gaps)
- Volume profile analysis
- Support/resistance level detection

### Data Validation
- Price anomaly detection
- Volume validation
- Cross-source verification
- Real-time quality monitoring

## Deployment
```bash
kubectl get pods -n crypto-data-collection | grep ohlc-collector
```

## Integration
- Feeds technical analysis calculations
- Provides base data for ML feature generation
- Supports backtesting and historical analysis
- Real-time trading signal generation