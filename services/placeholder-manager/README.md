# Centralized Placeholder Manager

## Overview
The Centralized Placeholder Manager is a dedicated service that ensures comprehensive data completeness across all crypto data collectors by proactively creating and managing placeholder records.

## Features
- **Comprehensive Placeholder Creation**: Creates placeholder records for all data types (macro, technical, onchain, sentiment)
- **Automated Scheduling**: Runs on configurable intervals to ensure continuous completeness
- **Gap Detection**: Identifies missing placeholder records and fills them automatically
- **Cleanup Management**: Removes old unfilled placeholder records to prevent data bloat
- **Health Monitoring**: Provides detailed status and completeness metrics
- **API Control**: RESTful endpoints for manual control and monitoring

## Architecture

### Service Components
1. **Placeholder Creation Engine**: Core logic for creating placeholder records across all collectors
2. **Scheduling System**: Automated execution based on configurable intervals  
3. **API Server**: REST endpoints for control and monitoring
4. **Metrics Collection**: Prometheus-compatible metrics for monitoring
5. **Health Checking**: Service health assessment and reporting

### Data Flow
```
Scheduled Trigger → Placeholder Manager → Database Tables → Completeness Tracking
       ↓                    ↓                   ↓                    ↓
   API Trigger         Gap Detection      Record Creation      Status Update
```

## Configuration

### Environment Variables
```bash
# Database Configuration
DB_HOST=127.0.0.1
DB_USER=news_collector  
DB_PASSWORD=99Rules!
DB_NAME=crypto_prices

# Service Configuration
MODE=scheduler                    # scheduler, api, or once
API_PORT=8080
ENABLE_PLACEHOLDERS=true
SCHEDULE_INTERVAL_HOURS=1

# Collector-Specific Configuration  
MACRO_LOOKBACK_DAYS=7            # Macro indicators lookback
TECHNICAL_LOOKBACK_HOURS=24      # Technical indicators lookback
ONCHAIN_LOOKBACK_DAYS=30         # Onchain data lookback
SENTIMENT_LOOKBACK_DAYS=7        # Sentiment analysis lookback
```

### Collector Configurations
Each collector type has specific configuration for placeholder creation:

#### Macro Indicators
- **Frequency**: Daily
- **Indicators**: VIX, DXY, FEDFUNDS, DGS10, DGS2, UNRATE, CPIAUCSL, GDP
- **Lookback**: 7 days (configurable)

#### Technical Indicators  
- **Frequency**: 5-minute intervals
- **Symbols**: Top 50 active symbols from price data
- **Lookback**: 24 hours (configurable)

#### Onchain Data
- **Frequency**: Daily
- **Symbols**: Top 20 crypto assets by market cap
- **Fields**: 25+ onchain metrics per symbol
- **Lookback**: 30 days (configurable)

#### Sentiment Analysis
- **Frequency**: Hourly
- **Symbols**: Same as technical indicators
- **Lookback**: 7 days (configurable)

## API Endpoints

### Health & Status
- `GET /health` - Kubernetes health check
- `GET /status` - Detailed service status with statistics
- `GET /completeness` - System-wide completeness summary
- `GET /metrics` - Prometheus metrics

### Control Operations
- `POST /create-placeholders` - Manually trigger comprehensive placeholder creation
- `POST /fill-gaps` - Detect and fill missing placeholder records
- `POST /cleanup/{days}` - Clean up placeholder records older than specified days

## Deployment

### Docker
```bash
# Build image
docker build -t crypto-data/placeholder-manager:latest .

# Run container
docker run -d \
  --name placeholder-manager \
  -p 8080:8080 \
  -e DB_HOST=mysql-host \
  -e DB_USER=news_collector \
  -e DB_PASSWORD=99Rules! \
  crypto-data/placeholder-manager:latest
```

### Kubernetes
```bash
# Apply deployment
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -n crypto-data -l app=placeholder-manager
kubectl logs -n crypto-data deployment/placeholder-manager

# Port forward for local testing
kubectl port-forward -n crypto-data svc/placeholder-manager-service 8080:8080
```

## Operation Modes

### Scheduler Mode (Default)
Runs continuous scheduling with API server:
```bash
MODE=scheduler python placeholder_manager.py
```

### API Only Mode
Runs only the API server without scheduling:
```bash
MODE=api python placeholder_manager.py
```

### One-Time Mode
Runs placeholder creation once and exits:
```bash
MODE=once python placeholder_manager.py
```

## Monitoring

### Prometheus Metrics
```
# Total placeholder records created
placeholder_manager_total_created

# Total errors encountered  
placeholder_manager_errors

# Service running status
placeholder_manager_running

# Average completeness per collector
macro_avg_completeness
technical_avg_completeness
onchain_avg_completeness
```

### Health Checks
The service provides multiple health indicators:
- **Service Health**: Based on error count and recent activity
- **Database Connectivity**: Connection status to MySQL
- **Completeness Metrics**: Average completeness across collectors
- **Last Run Status**: Timestamp and results of last execution

## Testing

### Automated Test Script
```bash
# Make executable and run
chmod +x test_placeholder_manager.sh
./test_placeholder_manager.sh
```

The test script validates:
- API endpoint availability
- Placeholder creation functionality  
- Database record verification
- Completeness calculation accuracy

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Get service status  
curl http://localhost:8080/status | jq

# Trigger placeholder creation
curl -X POST http://localhost:8080/create-placeholders

# Check completeness
curl http://localhost:8080/completeness | jq
```

## Database Schema

### Placeholder Record Structure
Each placeholder record contains:
- **Primary Keys**: Specific to each table (symbol, date/timestamp, indicator)
- **Data Fields**: Set to NULL for placeholder records
- **data_completeness_percentage**: Set to 0.0 for empty placeholders
- **data_source**: Set to 'placeholder_manager' for identification
- **created_at/collected_at**: Timestamp of placeholder creation

### Completeness Tracking
Completeness is calculated as:
```sql
completeness_percentage = (filled_fields / total_expected_fields) * 100
```

## Integration

### With Existing Collectors
The placeholder manager works alongside existing collectors:
1. **Before Collection**: Ensures placeholder records exist
2. **During Collection**: Collectors update placeholder records with actual data
3. **After Collection**: Completeness percentage is recalculated
4. **Monitoring**: Tracks which records remain as placeholders vs filled

### With Monitoring Systems
- **Grafana Dashboards**: Visualize completeness trends
- **Alert Manager**: Alert on low completeness thresholds
- **Prometheus**: Scrape metrics for long-term storage

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check environment variables
env | grep DB_

# Check database connectivity
mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD -e "SELECT 1"

# Check logs
kubectl logs -n crypto-data deployment/placeholder-manager
```

#### No Placeholders Created
```bash
# Verify ENABLE_PLACEHOLDERS setting
curl http://localhost:8080/status | jq .config

# Check for database errors
curl http://localhost:8080/status | jq .stats.errors

# Run manual creation
curl -X POST http://localhost:8080/create-placeholders
```

#### High Error Count
```bash
# Check service status
curl http://localhost:8080/status | jq .health

# Review database locks
mysql -h$DB_HOST -u$DB_USER -p$DB_PASSWORD -e "SHOW PROCESSLIST"

# Restart service
kubectl rollout restart deployment/placeholder-manager -n crypto-data
```

## Performance Considerations

### Resource Usage
- **Memory**: 256-512MB typical usage
- **CPU**: Low usage except during placeholder creation bursts
- **Database**: Creates batch INSERT operations, minimal impact
- **Network**: Low bandwidth requirements

### Scaling
- Service is designed as singleton (replicas: 1)
- Database operations use batch processing
- Scheduling prevents overlapping executions
- Cleanup operations maintain manageable data volumes

### Optimization
- Uses `INSERT IGNORE` to prevent duplicate creation
- Batch processes multiple records per transaction
- Configurable lookback periods to limit scope
- Automatic cleanup of old unfilled placeholders

## Future Enhancements

### Planned Features
- **Intelligent Gap Detection**: ML-based prediction of expected data points
- **Priority-Based Backfill**: Prioritize placeholder filling based on importance
- **Cross-Collector Dependencies**: Understand data dependencies between collectors
- **Historical Analysis**: Trend analysis of completeness over time

### Integration Opportunities
- **Data Quality Scoring**: Enhanced metrics beyond simple completeness
- **Anomaly Detection**: Identify unusual gaps or patterns
- **Automated Backfill**: Trigger specific collector runs for important gaps
- **Business Intelligence**: Connect completeness to business impact metrics