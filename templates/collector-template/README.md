# Standardized Collector Template Documentation

This template provides a comprehensive foundation for all data collectors in the crypto data collection system. It ensures consistency, observability, and maintainability across all collection services.

## Template Components

### 1. Base Collector Template (`base_collector_template.py`)
**Purpose**: Abstract base class that all collectors must inherit from

**Key Features**:
- **Structured Logging**: Full Loki integration with configurable levels (trace/debug/info/warning/error/critical/none)
- **Prometheus Metrics**: Comprehensive metrics for collection operations, API calls, database operations
- **Health & Status Endpoints**: `/health`, `/status`, `/logs`, `/metrics`
- **Backfill Capabilities**: `/backfill` endpoint with date range and symbol filtering
- **Manual Collection**: `/collect` endpoint for on-demand collection
- **Database Management**: Connection pooling, transaction management, error handling
- **Configuration Management**: Environment-based configuration with sensible defaults
- **Rate Limiting**: Token bucket rate limiter for API calls
- **Circuit Breaker**: Automatic failure detection and recovery for external services
- **Data Validation**: Schema validation, duplicate detection, data quality reporting
- **Performance Monitoring**: Real-time performance metrics and system resource tracking
- **Alerting Integration**: Webhook-based alert notifications for critical events
- **Graceful Shutdown**: Signal handling for clean service termination

**Required Implementation Methods**:
```python
async def collect_data(self) -> int:
    """Collect data from the source. Returns number of records collected."""
    
async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
    """Backfill missing data. Returns number of records backfilled."""
    
async def _get_table_status(self, cursor) -> Dict[str, Any]:
    """Get status of tables used by this collector."""
    
async def _analyze_missing_data(self, start_date, end_date, symbols) -> List[Dict]:
    """Analyze what data is missing for backfill."""
    
async def _estimate_backfill_records(self, start_date, end_date, symbols) -> int:
    """Estimate number of records that would be backfilled."""
    
async def _get_required_fields(self) -> List[str]:
    """Get required fields for data validation."""
    
async def _generate_data_quality_report(self) -> DataQualityReport:
    """Generate comprehensive data quality report."""
```

### 2. Kubernetes Template (`k8s/deployment-template.yaml`)
**Purpose**: Standardized K8s deployment configuration

**Key Features**:
- **Central Configuration**: Base ConfigMap for shared settings
- **Environment-Specific Secrets**: Template for credentials management
- **Resource Management**: Configurable CPU/memory limits
- **Health Probes**: Liveness and readiness probes
- **Service Discovery**: ClusterIP service with proper labels
- **Prometheus Integration**: ServiceMonitor for automatic metrics scraping

### 3. Example Implementation (`examples/news_collector_example.py`)
**Purpose**: Complete working example showing how to use the template

**Features Demonstrated**:
- RSS feed processing with multiple sources
- Batch processing for efficiency
- Error handling and recovery
- Database operations with duplicate handling
- Custom configuration extension

## Configuration System

### Base Configuration (Applied to All Collectors)
```yaml
# Collection Settings
COLLECTION_INTERVAL: "900"        # 15 minutes
BACKFILL_BATCH_SIZE: "100"
COLLECTOR_BEGINNING_DATE: "2023-01-01"

# Logging Settings
LOG_LEVEL: "trace"                # trace/debug/info/warning/error/critical/none
LOG_FORMAT: "json"                # json/console
ENABLE_AUDIT_LOGGING: "true"

# Database Settings
MYSQL_HOST: "host.docker.internal"
MYSQL_PORT: "3306"
MYSQL_DATABASE: "crypto_prices"
CONNECTION_POOL_SIZE: "10"
QUERY_TIMEOUT: "30"
BATCH_COMMIT_SIZE: "1000"

# Rate Limiting and Circuit Breaker
ENABLE_RATE_LIMITING: "true"
API_RATE_LIMIT_PER_MINUTE: "60"
CIRCUIT_BREAKER_FAILURE_THRESHOLD: "5"
CIRCUIT_BREAKER_TIMEOUT: "60"

# Data Validation and Quality
ENABLE_DATA_VALIDATION: "true"
ENABLE_DUPLICATE_DETECTION: "true"
DATA_RETENTION_DAYS: "365"

# Alerting and Notifications
ENABLE_ALERTING: "false"
ALERT_WEBHOOK_URL: ""             # Set webhook URL for alerts
ALERT_ERROR_THRESHOLD: "10"
```

### Collector-Specific Configuration
Each collector can extend the base configuration by:
1. Creating a custom config class inheriting from `CollectorConfig`
2. Adding collector-specific environment variables to K8s deployment
3. Implementing collector-specific validation and defaults

## API Endpoints

All collectors will provide these standardized endpoints:

### Health & Status
- `GET /health` - Simple health check with database connectivity
- `GET /status` - Detailed status including metrics and configuration
- `GET /logs?level=info&limit=100&since=ISO8601` - Log access (Loki integration)
- `GET /metrics` - Prometheus metrics in standard format
- `GET /data-quality` - Comprehensive data quality report
- `GET /performance` - Real-time performance metrics
- `GET /circuit-breaker-status` - Circuit breaker state and failure information

### Operations
- `POST /collect` - Trigger manual collection
- `POST /backfill` - Backfill missing data with date range and symbol filtering
- `POST /alert` - Send alert notification via webhook
- `POST /validate-data` - Validate data structure and content

### Example Responses
```json
// GET /health
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "enhanced-crypto-news",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "database_connected": true,
  "last_collection": "2024-01-15T10:15:00Z",
  "last_successful_collection": "2024-01-15T10:15:00Z",
  "collection_errors": 0
}

// GET /data-quality
{
  "total_records": 10000,
  "valid_records": 9950,
  "invalid_records": 50,
  "duplicate_records": 25,
  "validation_errors": ["Missing required field: price"],
  "data_quality_score": 99.25
}

// GET /performance
{
  "avg_collection_time": 12.5,
  "success_rate": 99.8,
  "error_rate": 0.2,
  "database_latency": 45.2,
  "api_latency": 156.7,
  "memory_usage_mb": 512.3,
  "cpu_usage_percent": 15.6
}

// POST /backfill
{
  "task_id": "uuid-here",
  "status": "started",
  "message": "Backfill operation started",
  "estimated_records": 1500,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-14T23:59:59Z"
}
```

## Logging Standards

### Structured Logging with Context
All log entries include:
- `service`: Service name
- `session_id`: Unique session identifier
- `timestamp`: ISO8601 timestamp
- `level`: Log level
- `message`: Human-readable message
- `context`: Additional structured data

### Example Log Entries
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "service": "enhanced-crypto-news",
  "session": "uuid-here",
  "message": "collection_started",
  "task_id": "uuid-here",
  "feeds": 4
}
```

### Log Levels Configuration
- **trace**: Detailed debugging (default for development)
- **debug**: Debug information
- **info**: General information
- **warning**: Warning conditions
- **error**: Error conditions
- **critical**: Critical errors
- **none**: Disable logging

## Metrics Standards

### Standard Metrics (All Collectors)
```
{service}_collection_requests_total{status="success|error"}
{service}_collection_duration_seconds
{service}_records_processed_total{operation="insert|update|delete"}
{service}_database_operations_total{operation="insert|query", status="success|error"}
{service}_api_requests_total{endpoint="url", status="success|error"}
{service}_backfill_operations_total{status="success|error"}
{service}_active_collections
```

### Custom Metrics
Collectors can add custom metrics using the same naming convention:
```python
self.custom_metric = Counter(
    f'{service_name}_custom_operation_total',
    'Description of custom metric',
    ['label1', 'label2']
)
```

## Database Integration

### Connection Management
- Automatic connection pooling
- Transaction management
- Error handling and retry logic
- Connection health monitoring

### Example Database Operations
```python
async def save_data(self, data):
    with self.get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO table ...", data)
        conn.commit()
        
        self.metrics['records_processed_total'].labels(operation='insert').inc()
        self.metrics['database_operations_total'].labels(
            operation='insert', 
            status='success'
        ).inc()
```

## Backfill System

### Automatic Gap Detection
The template provides built-in gap analysis:
```python
missing_periods = await self._analyze_missing_data(start_date, end_date, symbols)
```

### Backfill Request Format
```json
{
  "start_date": "2024-01-01",          // Optional, defaults to COLLECTOR_BEGINNING_DATE
  "end_date": "2024-01-14",            // Optional, defaults to yesterday
  "symbols": ["BTC", "ETH"],           // Optional, defaults to all symbols
  "force": false                       // Optional, force re-collection of existing data
}
```

### Backfill Processing
- Chunked processing for large date ranges
- Rate limiting to avoid API overload
- Progress tracking via logs and metrics
- Automatic retry on failures

## Error Handling

### Standardized Error Response
```python
try:
    # Collection logic
    pass
except Exception as e:
    self.logger.error("operation_failed", error=str(e), context=additional_context)
    self.metrics['collection_requests_total'].labels(status='error').inc()
    raise
```

### Fault Tolerance
- Automatic retry with exponential backoff
- Circuit breaker for external APIs
- Graceful degradation on partial failures
- Comprehensive error logging with context

## Deployment Guidelines

### 1. Create Collector Implementation
```python
class MyCollector(BaseCollector):
    def __init__(self):
        config = MyCollectorConfig.from_env()
        super().__init__(config)
    
    async def collect_data(self) -> int:
        # Implementation here
        pass
```

### 2. Customize Kubernetes Configuration
1. Copy `k8s/deployment-template.yaml`
2. Replace `COLLECTOR_NAME` with your service name
3. Add collector-specific environment variables
4. Adjust resource limits based on needs
5. Add collector-specific dependencies to installation script

### 3. Deploy to Kubernetes
```bash
# Apply base configuration (once per cluster)
kubectl apply -f collector-base-config.yaml

# Deploy collector
kubectl apply -f my-collector-k8s.yaml
```

### 4. Verify Deployment
- Check health endpoint: `curl http://service:8000/health`
- Verify metrics: `curl http://service:8000/metrics`
- Monitor logs via Loki
- Check Prometheus for metrics

## Integration with Monitoring Stack

### Loki Integration
- Logs automatically forwarded to Loki with proper labels
- Query logs: `{service="enhanced-crypto-news"} |= "collection_started"`
- Access via `/logs` endpoint or direct Loki API

### Prometheus Integration
- Automatic service discovery via ServiceMonitor
- Standard metrics available in Grafana
- Alert rules can be configured for service health

### Grafana Dashboards
- Service health overview
- Collection performance metrics
- Database operation metrics
- Custom collector-specific dashboards

## Migration from Legacy Collectors

### Step-by-Step Migration
1. **Analyze Current Collector**: Identify core collection logic
2. **Extend Base Template**: Create new collector class
3. **Implement Required Methods**: Move collection logic to template methods
4. **Test Functionality**: Verify all collection scenarios work
5. **Deploy Side-by-Side**: Run both versions temporarily
6. **Verify Data Integrity**: Ensure no data loss during transition
7. **Switch Traffic**: Update service selectors
8. **Remove Legacy**: Clean up old deployment

### Validation Checklist
- [ ] Health endpoint responds correctly
- [ ] Collection runs successfully
- [ ] Database operations work
- [ ] Metrics are exported
- [ ] Logs are structured properly
- [ ] Backfill functionality works
- [ ] Error handling is comprehensive
- [ ] Resource usage is appropriate

## Best Practices

### Code Organization
- Keep collection logic in abstract methods
- Use async/await for I/O operations
- Implement proper error boundaries
- Add comprehensive logging at key points

### Performance Considerations
- Use batch processing for large datasets
- Implement appropriate rate limiting
- Monitor resource usage via metrics
- Use connection pooling for database operations

### Security
- Store sensitive data in Kubernetes secrets
- Use least-privilege database credentials
- Implement proper input validation
- Log security-relevant events

### Monitoring
- Add custom metrics for business logic
- Use structured logging with context
- Implement proper alert thresholds
- Monitor both success and failure scenarios

This template ensures all collectors follow consistent patterns while providing the flexibility to implement collector-specific logic. It promotes maintainability, observability, and operational excellence across the entire data collection infrastructure.