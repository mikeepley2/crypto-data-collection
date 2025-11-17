# Placeholder Creation Strategy - Implementation Guide

**Status:** November 10, 2025  
**Purpose:** Guide for implementing automatic placeholder record creation across all data collectors

---

## Overview

The placeholder creation strategy ensures comprehensive data collection completeness tracking by proactively creating blank records for all expected data points. This provides:

- **100% visibility** into expected vs actual data coverage
- **Proactive gap management** before collection failures become large gaps
- **Enhanced backfill prioritization** based on known missing data points
- **Real-time monitoring** of collection health and data quality

---

## Implementation Architecture

### 1. **Template-Based Approach**

All collectors inherit from the base template at `templates/collector_template_with_placeholders.py`:

```python
class BaseDataCollectorWithPlaceholders:
    """
    Base template providing:
    - Automatic placeholder creation
    - Completeness percentage tracking
    - Gap detection and backfill
    - Health monitoring
    - FastAPI endpoints for control/monitoring
    """
```

### 2. **Collector-Specific Implementation**

Each collector implements these abstract methods:

```python
def get_expected_data_points(self, start_time, end_time) -> List[Dict]:
    """Return expected data points for time range"""
    
def create_placeholder_record(self, data_point: Dict) -> bool:
    """Create placeholder for specific data point"""
    
def collect_real_data(self, backfill_days=None) -> int:
    """Collect real data and update placeholders"""
    
def calculate_record_completeness(self, record_data: Dict) -> float:
    """Calculate completeness percentage (0-100)"""
```

### 3. **Configuration Environment Variables**

```yaml
# Enable/disable placeholder creation
ENSURE_PLACEHOLDERS: "true"

# How far back to create placeholders
PLACEHOLDER_LOOKBACK_DAYS: "7"     # For daily/onchain collectors
PLACEHOLDER_LOOKBACK_HOURS: "24"   # For hourly/technical collectors

# Maximum backfill to prevent runaway operations
MAX_BACKFILL_DAYS: "30"
```

---

## Collector-Specific Implementations

### Macro Indicators Collector

**Frequency:** Daily  
**Placeholders:** One record per indicator per day  
**Expected Data Points:** VIX, DXY, FEDFUNDS, DGS10, UNRATE, etc.

```python
def get_expected_data_points(self, start_time, end_time):
    data_points = []
    current_date = start_time.date()
    
    while current_date <= end_time.date():
        for indicator in ['VIX', 'DXY', 'FEDFUNDS', 'DGS10', 'UNRATE']:
            data_points.append({
                'indicator_name': indicator,
                'indicator_date': current_date,
                'data_type': 'macro'
            })
        current_date += timedelta(days=1)
    
    return data_points

def create_placeholder_record(self, data_point):
    cursor.execute(\"\"\"
        INSERT IGNORE INTO macro_indicators 
        (indicator_name, indicator_date, value, data_source, 
         data_completeness_percentage, created_at)
        VALUES (%s, %s, NULL, 'placeholder_auto', 0.0, NOW())
    \"\"\", (data_point['indicator_name'], data_point['indicator_date']))
```

### Technical Indicators Collector

**Frequency:** 5 minutes  
**Placeholders:** One record per symbol per 5-minute interval  
**Expected Data Points:** All active trading symbols with technical indicators

```python
def get_expected_data_points(self, start_time, end_time):
    symbols = self.get_active_symbols()
    data_points = []
    
    current_time = start_time
    while current_time <= end_time:
        # Round to nearest 5-minute mark
        rounded_time = current_time.replace(
            minute=(current_time.minute // 5) * 5, 
            second=0, microsecond=0
        )
        
        for symbol in symbols:
            data_points.append({
                'symbol': symbol,
                'timestamp': rounded_time,
                'data_type': 'technical'
            })
        
        current_time += timedelta(minutes=5)
    
    return data_points

def create_placeholder_record(self, data_point):
    cursor.execute(\"\"\"
        INSERT IGNORE INTO technical_indicators
        (symbol, timestamp, rsi_14, sma_20, sma_50, ema_12, ema_26,
         macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower,
         data_completeness_percentage, data_source)
        VALUES (%s, %s, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 
                NULL, NULL, NULL, 0.0, 'placeholder_auto')
    \"\"\", (data_point['symbol'], data_point['timestamp']))
```

### Onchain Data Collector

**Frequency:** 6 hours  
**Placeholders:** One record per symbol per 6-hour interval  
**Expected Data Points:** All supported cryptocurrencies with onchain metrics

```python
def get_expected_data_points(self, start_time, end_time):
    symbols = self.get_supported_symbols()
    data_points = []
    
    current_time = start_time
    while current_time <= end_time:
        # Round to nearest 6-hour mark
        rounded_time = current_time.replace(
            hour=(current_time.hour // 6) * 6,
            minute=0, second=0, microsecond=0
        )
        
        for symbol in symbols:
            data_points.append({
                'symbol': symbol,
                'data_date': rounded_time.date(),
                'data_type': 'onchain'
            })
        
        current_time += timedelta(hours=6)
    
    return data_points

def create_placeholder_record(self, data_point):
    # Create placeholder with all 46-50 onchain fields set to NULL
    placeholder_fields = ', '.join(['NULL'] * 46)  # Adjust count as needed
    
    cursor.execute(f\"\"\"
        INSERT IGNORE INTO crypto_onchain_data
        (symbol, data_date, active_addresses_24h, transaction_count_24h,
         exchange_net_flow_24h, price_volatility_7d, market_cap_realized,
         mvrv_ratio, {placeholder_fields}, 
         data_completeness_percentage, data_source, created_at)
        VALUES (%s, %s, {placeholder_fields}, 0.0, 'placeholder_auto', NOW())
    \"\"\", (data_point['symbol'], data_point['data_date']))
```

---

## Collection Workflow

### 1. **Startup Sequence**

```python
def run_scheduler(self):
    # Step 1: Auto-detect and backfill gaps on startup
    self.auto_gap_detection_and_backfill()
    
    # Step 2: Schedule regular collections
    schedule.every(self.collection_interval).do(self.run_collection_with_placeholders)
    
    # Step 3: Schedule health monitoring
    schedule.every(5).minutes.do(self.write_health_file)
```

### 2. **Collection Cycle**

```python
def run_collection_with_placeholders(self, backfill_days=None):
    # Step 1: Ensure placeholder records exist
    placeholders_created = self.ensure_placeholder_records()
    
    # Step 2: Collect real data and update placeholders
    records_collected = self.collect_real_data(backfill_days)
    
    # Step 3: Update completeness percentages
    # (Handled automatically in collect_real_data)
    
    # Step 4: Update health metrics
    self.write_health_file()
```

### 3. **Gap Detection and Backfill**

```python
def auto_gap_detection_and_backfill(self):
    gap_hours = self.detect_gap()
    
    if gap_hours > expected_interval_hours * 2:
        gap_days = min(int(gap_hours / 24) + 1, self.max_backfill_limit)
        logger.warning(f\"Triggering backfill for {gap_days} days\")
        self.run_collection_with_placeholders(backfill_days=gap_days)
```

---

## Completeness Calculation

### Standard Completeness Formula

```python
def calculate_record_completeness(self, record_data: Dict) -> float:
    \"\"\"
    Calculate completeness percentage based on populated fields
    \"\"\"
    # Define required fields for this record type
    required_fields = self.get_required_fields()
    
    # Count populated fields (not NULL, not empty string)
    populated = sum(1 for field in required_fields 
                   if record_data.get(field) is not None 
                   and str(record_data.get(field)).strip() != '')
    
    return (populated / len(required_fields)) * 100.0
```

### Collector-Specific Examples

**Macro Indicators:**
```python
def get_required_fields(self):
    return ['indicator_name', 'indicator_date', 'value', 'data_source']

# Example: VIX record with value = 25.4
# Completeness = 4/4 * 100 = 100%
```

**Technical Indicators:**
```python
def get_required_fields(self):
    return ['symbol', 'timestamp', 'rsi_14', 'sma_20', 'sma_50', 
            'ema_12', 'ema_26', 'macd', 'macd_signal', 'bb_upper', 
            'bb_middle', 'bb_lower']

# Example: BTC record with RSI + SMA populated, others NULL
# Completeness = 4/12 * 100 = 33.3%
```

**Onchain Data:**
```python
def get_required_fields(self):
    return ['symbol', 'data_date', 'active_addresses_24h', 
            'transaction_count_24h', 'exchange_net_flow_24h',
            'price_volatility_7d', 'market_cap_realized', 'mvrv_ratio']
            # ... plus 38 more fields

# Example: ETH record with 23 of 46 fields populated
# Completeness = 23/46 * 100 = 50%
```

---

## Monitoring and Alerting

### Health Score Calculation

```python
def calculate_health_score(self) -> float:
    \"\"\"
    Weighted health score (0-100) based on:
    - Data freshness (40%)
    - Average completeness (40%) 
    - Error rate (20%)
    \"\"\"
    freshness_score = max(0, 100 - (gap_hours / expected_hours) * 20)
    completeness_score = avg_completeness_percentage
    error_score = max(0, 100 - (error_rate * 200))
    
    return (freshness_score * 0.4 + 
            completeness_score * 0.4 + 
            error_score * 0.2)
```

### FastAPI Monitoring Endpoints

```python
# Health check for Kubernetes
GET /health 
→ {\"status\": \"ok\", \"service\": \"macro-collector\"}

# Detailed status 
GET /status
→ {\"health\": {\"score\": 87.5, \"gap_hours\": 0.5}, ...}

# Prometheus metrics
GET /metrics
→ macro_collector_health_score 87.5
  macro_collector_gap_hours 0.5
  macro_collector_placeholders_created 147

# Manual triggers
POST /collect          # Trigger immediate collection
POST /collect/7        # Trigger 7-day backfill
POST /placeholders     # Create missing placeholders
POST /gap-check        # Run gap detection
```

### Alert Thresholds

- **Critical**: Health score < 50, Gap > 6 hours
- **Warning**: Health score < 75, Gap > 2 hours  
- **Info**: Completeness < 80%, Error rate > 5%

---

## Database Schema Updates

### Required Completeness Columns

```sql
-- Add to all collection tables
ALTER TABLE macro_indicators 
ADD COLUMN data_completeness_percentage DECIMAL(5,2) DEFAULT 0.0;

ALTER TABLE technical_indicators 
ADD COLUMN data_completeness_percentage DECIMAL(5,2) DEFAULT 0.0;

ALTER TABLE crypto_onchain_data 
ADD COLUMN data_completeness_percentage DECIMAL(5,2) DEFAULT 0.0;
```

### Monitoring Views

```sql
-- System-wide completeness summary
CREATE VIEW completeness_summary AS
SELECT 
    'macro' as collector_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
    AVG(data_completeness_percentage) as avg_completeness
FROM macro_indicators 
WHERE indicator_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)

UNION ALL

SELECT 
    'technical' as collector_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
    AVG(data_completeness_percentage) as avg_completeness
FROM technical_indicators 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)

UNION ALL

SELECT 
    'onchain' as collector_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
    AVG(data_completeness_percentage) as avg_completeness
FROM crypto_onchain_data 
WHERE data_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);
```

---

## Deployment Configuration

### Kubernetes ConfigMap Updates

```yaml
# k8s/collectors/collector-configmaps.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: macro-collector-config
data:
  # Placeholder configuration
  ENSURE_PLACEHOLDERS: \"true\"
  PLACEHOLDER_LOOKBACK_DAYS: \"7\"
  MAX_BACKFILL_DAYS: \"30\"
  
  # Collection configuration  
  COLLECTION_INTERVAL: \"1hour\"
  FRED_API_KEY: \"your-api-key\"
```

### Environment Variable Summary

| Variable | Macro | Technical | Onchain | Description |
|----------|-------|-----------|---------|-------------|
| `ENSURE_PLACEHOLDERS` | true | true | true | Enable placeholder creation |
| `PLACEHOLDER_LOOKBACK_DAYS` | 7 | - | 30 | Days to look back for placeholders |
| `PLACEHOLDER_LOOKBACK_HOURS` | - | 24 | - | Hours to look back for placeholders |
| `MAX_BACKFILL_DAYS` | 30 | 7 | 90 | Maximum backfill period |
| `COLLECTION_INTERVAL` | 1hour | 5min | 6hour | Collection frequency |

---

## Testing and Validation

### Unit Tests

```python
def test_placeholder_creation():
    \"\"\"Test that placeholders are created correctly\"\"\"
    collector = MacroCollector()
    
    # Test expected data points generation
    start_time = datetime(2025, 11, 1)
    end_time = datetime(2025, 11, 3)
    points = collector.get_expected_data_points(start_time, end_time)
    
    # Should have 3 days * 5 indicators = 15 data points
    assert len(points) == 15
    assert points[0]['indicator_name'] in ['VIX', 'DXY', 'FEDFUNDS']

def test_completeness_calculation():
    \"\"\"Test completeness percentage calculation\"\"\"
    record_data = {
        'indicator_name': 'VIX',
        'indicator_date': '2025-11-10',
        'value': 25.4,
        'data_source': 'FRED'
    }
    
    completeness = collector.calculate_record_completeness(record_data)
    assert completeness == 100.0  # All required fields populated
```

### Integration Tests

```bash
# Test placeholder creation
curl -X POST http://localhost:8000/placeholders

# Verify placeholders in database
mysql -e \"SELECT COUNT(*) FROM macro_indicators WHERE data_completeness_percentage = 0\"

# Test collection with placeholders
curl -X POST http://localhost:8000/collect

# Verify completion updates
mysql -e \"SELECT AVG(data_completeness_percentage) FROM macro_indicators WHERE data_source != 'placeholder_auto'\"
```

---

## Performance Considerations

### Placeholder Volume Estimates

**Macro Collector (7-day lookback):**
- 7 days × 5 indicators = 35 placeholders per run
- Minimal database impact

**Technical Collector (24-hour lookback):**  
- 24 hours × 12 intervals/hour × 50 symbols = 14,400 placeholders per run
- Moderate database impact - consider batching

**Onchain Collector (30-day lookback):**
- 30 days × 4 intervals/day × 50 symbols = 6,000 placeholders per run  
- Manageable database impact

### Optimization Strategies

1. **Batch Operations**: Use `INSERT IGNORE` with multiple VALUES
2. **Index Strategy**: Ensure unique indexes on time/symbol combinations
3. **Cleanup Logic**: Remove old placeholders that remain unfilled
4. **Conditional Creation**: Only create placeholders during active trading hours

---

## Migration Path

### Phase 1: Template and Core Infrastructure (Complete)
- ✅ Base template created
- ✅ Documentation updated
- ✅ Configuration patterns defined

### Phase 2: Individual Collector Updates (Next)
1. Update macro collector with placeholder logic
2. Update technical collector with placeholder logic  
3. Update enhanced onchain collector with placeholder logic
4. Deploy and test each collector individually

### Phase 3: Centralized Management
1. Create centralized placeholder manager service
2. Implement cross-collector consistency checks
3. Add advanced monitoring and alerting

### Phase 4: Optimization and Enhancement
1. Performance optimization based on production metrics
2. Advanced completeness algorithms
3. Machine learning-based gap prediction

---

*This guide provides comprehensive implementation details for the placeholder creation strategy. Use the base template and examples to implement placeholder logic in each data collector for complete visibility into data collection completeness.*