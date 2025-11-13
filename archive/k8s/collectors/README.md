# ML Market Collector - K8s Deployment

## Overview

The ML Market Collector is a specialized data collection service that gathers traditional market data highly correlated with cryptocurrency movements. This collector provides **~40 ML features** for crypto trading models by tracking major market indices, ETFs, currencies, and volatility indicators.

## Features Collected

### Traditional Market Assets (12 assets × 3 metrics = 36 features)
- **Equity Indices**: QQQ (NASDAQ), SPY (S&P 500), IWM (Russell 2000)
- **Innovation ETFs**: ARKK (Innovation), ARKQ (Robotics), ARKG (Genomics)
- **Bonds**: HYG (High Yield), LQD (Investment Grade), TLT (Treasury)
- **Commodities**: GLD (Gold), SLV (Silver), USO (Oil)
- **Currencies**: EUR/USD, GBP/USD, JPY/USD
- **Volatility**: VIX, DXY (Dollar Index)

### Calculated ML Indicators (7 features)
1. **Risk-On/Risk-Off Ratio**: (QQQ + HYG) / (VIX + TLT)
2. **Innovation Premium**: ARKK / QQQ ratio
3. **Tech Leadership**: QQQ / SPY ratio  
4. **Credit Spreads**: HYG vs LQD performance differential
5. **Flight to Quality**: Gold/Treasury correlation strength
6. **Dollar Strength Impact**: DXY momentum effect
7. **Market Breadth**: Large cap vs small cap ratio (SPY/IWM)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   yfinance      │    │   Database      │
│   Endpoints     │────│   Data Source   │────│   Storage       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Scheduler     │──────────────┘
                        │   (30 min)      │
                        └─────────────────┘
```

## Correlation Analysis

Based on historical analysis, these assets show strong correlation with crypto markets:

| Asset | Crypto Correlation | Usage |
|-------|-------------------|-------|
| ARKK | 80% | Innovation sector sentiment |
| QQQ | 75% | Tech sector performance |
| VIX | -65% | Market fear/volatility (inverse) |
| DXY | -55% | Dollar strength (inverse) |
| HYG | 70% | Risk appetite indicator |
| TLT | -45% | Safe haven flows (inverse) |

## Deployment

### Prerequisites
- Kubernetes cluster with kubectl access
- Centralized database configuration (ConfigMaps and Secrets)
- `kustomize` tool installed

### Quick Deploy
```bash
cd k8s/collectors
./deploy-ml-market-collector.sh
```

### Manual Deploy
```bash
# Apply with kustomize
kubectl apply -k k8s/collectors --namespace crypto-data-collection

# Wait for deployment
kubectl wait --for=condition=available deployment/ml-market-collector -n crypto-data-collection --timeout=300s
```

## Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `COLLECTION_INTERVAL_MINUTES` | Data collection frequency | 30 |
| `ML_FEATURE_COUNT_TARGET` | Expected feature count | 35 |
| `HIGH_CORRELATION_THRESHOLD` | High correlation cutoff | 0.65 |
| `LOG_LEVEL` | Logging level | INFO |
| `YFINANCE_REQUEST_DELAY` | Rate limiting delay | 0.1 |

### Database Integration
Uses centralized database configuration:
- **ConfigMap**: `centralized-db-config`
- **Secret**: `centralized-db-secrets` 
- **Connection**: Shared database pool with other collectors

## Monitoring

### Health Check
```bash
./monitor-ml-market-collector.sh
```

### API Endpoints
After port-forwarding (`kubectl port-forward service/ml-market-collector 8080:8000`):

- **Health**: `GET /health` - Service health status
- **Collect**: `POST /collect` - Trigger manual collection
- **ML Features**: `GET /ml-features` - Current feature values
- **Status**: `GET /status` - Collection statistics

### Manual Commands
```bash
# View logs
kubectl logs -n crypto-data-collection deployment/ml-market-collector -f

# Test API health
kubectl port-forward -n crypto-data-collection service/ml-market-collector 8080:8000
curl http://localhost:8080/health

# Trigger collection
curl -X POST http://localhost:8080/collect

# Get ML features
curl http://localhost:8080/ml-features
```

## Scheduling

- **Automatic**: CronJob runs every 30 minutes
- **Manual**: POST to `/collect` endpoint
- **Schedule**: Configurable via `COLLECTION_INTERVAL_MINUTES`

## Resource Requirements

| Resource | Request | Limit |
|----------|---------|-------|
| Memory | 512Mi | 1Gi |
| CPU | 200m | 500m |
| Storage | None (external DB) | - |

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   kubectl get configmap centralized-db-config -n crypto-data-collection
   kubectl get secret centralized-db-secrets -n crypto-data-collection
   ```

2. **API Rate Limiting**
   - Increase `YFINANCE_REQUEST_DELAY` in ConfigMap
   - Check yfinance API limits

3. **Missing Features**
   - Check `/status` endpoint for collection errors
   - Verify asset symbols are valid
   - Monitor logs for yfinance failures

4. **Pod Crashes**
   ```bash
   kubectl describe pod -n crypto-data-collection -l app=ml-market-collector
   kubectl logs -n crypto-data-collection deployment/ml-market-collector --previous
   ```

### Performance Tuning

- **Scale up**: `kubectl scale deployment/ml-market-collector --replicas=2`
- **Resource adjustment**: Edit deployment resource requests/limits
- **Collection frequency**: Adjust `COLLECTION_INTERVAL_MINUTES`

## Integration with Materialized Views

The collected ML features integrate with the materialized updater system:

```sql
-- Example ML features in materialized view
SELECT 
    timestamp,
    symbol,
    -- Crypto-native features (existing)
    price, volume, market_cap,
    -- Traditional market ML features (new)
    ml_risk_on_ratio,
    ml_innovation_premium,
    ml_tech_leadership,
    ml_credit_spreads,
    ml_vix_fear_index,
    ml_dollar_strength,
    -- Asset correlations
    ml_nasdaq_correlation,
    ml_arkk_correlation,
    ml_gold_correlation
FROM crypto_ml_features_materialized;
```

## Development

### Local Testing
```bash
# Install dependencies
pip install -r services/market-collection/requirements.txt

# Run locally
cd services/market-collection
python ml_market_collector.py
```

### Adding New Assets
1. Update `TRACKED_ASSETS` in `ml_market_collector.py`
2. Add correlation analysis in `analyze_ml_market_value.py`
3. Update expected feature count in ConfigMap
4. Redeploy with `kubectl rollout restart deployment/ml-market-collector`

### Custom Indicators
1. Add calculation logic in `calculate_ml_indicators()`
2. Update database schema if needed
3. Test with `/ml-features` endpoint
4. Monitor feature count target

## Scaling Considerations

- **Single replica recommended**: Avoids duplicate data collection
- **Horizontal scaling**: Add read replicas for API endpoints only
- **Vertical scaling**: Increase resources for faster collection
- **Database scaling**: Ensure connection pool can handle load

---

**Generated Features**: ~40 ML indicators for crypto trading models  
**Data Sources**: Traditional markets with high crypto correlation  
**Update Frequency**: Configurable, default 30 minutes  
**Integration**: Centralized config and shared database pooling