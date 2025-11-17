# ML Market Collection Service

## Overview
Traditional market data collector providing comprehensive coverage of equities, bonds, commodities, currencies, and sector ETFs for machine learning model training.

## Asset Coverage
### Sector ETFs
- **XLE**: Energy sector
- **XLF**: Financial sector  
- **XLK**: Technology sector
- **XLP**: Consumer staples
- **XLY**: Consumer discretionary

### Market Indices
- **SPY**: S&P 500 ETF
- **QQQ**: NASDAQ-100 ETF
- **VIX**: Volatility index
- **DXY**: US Dollar index

### Bonds & Fixed Income
- **TLT**: 20+ Year Treasury Bond ETF
- **HYG**: High Yield Corporate Bond ETF
- **LQD**: Investment Grade Corporate Bond ETF
- **TNX**: 10-Year Treasury Yield

### Commodities
- **GLD**: Gold ETF
- **SLV**: Silver ETF  
- **USO**: Oil ETF
- **Natural Gas**: Energy commodity
- **Copper**: Industrial metal

### Currencies
- **EUR/USD, JPY/USD, GBP/USD**
- **AUD/USD, CAD/USD, CHF/USD**

## Configuration
- **Schedule**: Every 30 minutes
- **Port**: 8000
- **Data Source**: Yahoo Finance API
- **Database**: Stores to `macro_indicators` table with ML_ prefix

## ML Features Generated
- Price levels and daily changes
- Volatility indicators
- Cross-asset correlations
- Momentum factors
- Risk measures

## Deployment
```bash
kubectl get pods -n crypto-data-collection | grep ml-market-collector
```