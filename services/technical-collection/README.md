# Technical Analysis Collection Service

## Overview
Comprehensive technical analysis service calculating 25+ technical indicators in real-time from price data for machine learning and trading applications.

## Technical Indicators Calculated
### Trend Indicators
- **Simple Moving Averages (SMA)**: 20, 50, 200 periods
- **Exponential Moving Averages (EMA)**: 12, 26 periods
- **MACD**: Moving Average Convergence Divergence
  - MACD Line (EMA12 - EMA26)
  - Signal Line (9-period EMA of MACD)
  - MACD Histogram

### Momentum Oscillators
- **RSI**: Relative Strength Index (14-period)
- **Stochastic**: %K and %D oscillators
- **Williams %R**: Momentum indicator
- **Rate of Change (ROC)**: Price momentum

### Volatility Indicators
- **Bollinger Bands**: Upper, middle (SMA20), lower bands
- **Average True Range (ATR)**: 14-period volatility
- **Bollinger Band Width**: Volatility measurement
- **Volatility Ratio**: Short vs long-term volatility

### Volume Indicators
- **Volume Weighted Average Price (VWAP)**
- **Volume SMA**: Volume moving averages
- **Price Volume Trend (PVT)**
- **On-Balance Volume (OBV)**

## Configuration
- **Processing Interval**: Real-time (triggered by price updates)
- **Port**: 8000
- **Data Input**: Price and volume data from OHLC collector
- **Database**: Stores to `technical_indicators` table

## Calculation Engine
### Real-time Processing
- Event-driven calculations
- Incremental updates for efficiency
- Historical data validation
- Multi-timeframe support

### Data Quality
- Input validation and sanitization
- Mathematical accuracy verification
- Boundary condition handling
- Error recovery and logging

## Deployment
```bash
kubectl get pods -n crypto-data-collection | grep technical-calculator
```

## ML Integration
- Features feed directly into ML models
- Real-time signal generation
- Historical backtesting support
- Cross-asset indicator calculations