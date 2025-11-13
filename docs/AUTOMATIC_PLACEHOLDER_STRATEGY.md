# Automatic Placeholder Record Creation Strategy

## Overview

Implement automatic creation of blank placeholder records to ensure comprehensive data collection completeness tracking and improve backfill prioritization.

## Implementation Strategy: Hybrid Approach

### 1. Collection Service Level (Primary)
Each collector creates placeholders for its own expected data points:

**Location:** In each collector's main collection function
**Timing:** Before attempting data collection
**Scope:** Service-specific expected records

### 2. Centralized Placeholder Service (Secondary) 
Handle cross-collector coordination and global placeholder management:

**Location:** New service `services/placeholder-manager/`
**Timing:** Scheduled runs (hourly) to catch missed placeholders
**Scope:** System-wide placeholder consistency

## Implementation Details

### A. Individual Collector Integration

#### Macro Collector Enhancement
```python
# services/macro-collection/macro_collector.py

def ensure_placeholder_records(cursor, target_date, data_source="placeholder_auto"):
    """Create placeholder records for all expected macro indicators"""
    
    for indicator_name in FRED_SERIES.keys():
        try:
            cursor.execute("""
                INSERT IGNORE INTO macro_indicators 
                (indicator_name, indicator_date, value, data_source, data_completeness_percentage, collected_at)
                VALUES (%s, %s, NULL, %s, 0.0, NOW())
            """, (indicator_name, target_date, data_source))
            
            if cursor.rowcount > 0:
                logger.info(f"Created placeholder for {indicator_name} on {target_date}")
        except Exception as e:
            logger.error(f"Error creating placeholder for {indicator_name}: {e}")

def collect_macro_indicators_with_placeholders(backfill_days=None):
    """Enhanced collection that ensures placeholders exist"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. First, ensure placeholder records exist for expected data points
        if backfill_days:
            # Create placeholders for backfill period
            for days_ago in range(backfill_days + 1):
                target_date = datetime.now().date() - timedelta(days=days_ago)
                ensure_placeholder_records(cursor, target_date, "backfill_placeholder")
        else:
            # Create placeholders for today
            ensure_placeholder_records(cursor, datetime.now().date(), "daily_placeholder")
        
        conn.commit()
        
        # 2. Now collect real data and update placeholders
        return collect_macro_indicators(backfill_days)
        
    finally:
        cursor.close()
        conn.close()
```

#### Technical Indicators Enhancement
```python
# services/technical-collection/technical_calculator.py

def ensure_technical_placeholders(cursor, symbol, target_datetime):
    """Create placeholder technical indicator records"""
    
    try:
        cursor.execute("""
            INSERT IGNORE INTO technical_indicators
            (symbol, timestamp, 
             rsi_14, sma_20, sma_50, ema_12, ema_26,
             macd, macd_signal, macd_histogram,
             bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vwap,
             data_completeness_percentage, data_source)
            VALUES (%s, %s, 
                   NULL, NULL, NULL, NULL, NULL,
                   NULL, NULL, NULL, 
                   NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                   0.0, 'placeholder_auto')
        """, (symbol, target_datetime))
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.debug(f"Error creating technical placeholder for {symbol}: {e}")
        return False

def calculate_indicators_with_placeholders(backfill_days=None):
    """Enhanced calculation that ensures placeholders exist"""
    
    # Get active symbols
    symbols = get_active_symbols()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create placeholders for expected calculation intervals
        if backfill_days:
            start_date = datetime.now() - timedelta(days=backfill_days)
        else:
            start_date = datetime.now() - timedelta(hours=1)  # Last hour
        
        # Create placeholders every 5 minutes for technical data
        current_time = start_date
        end_time = datetime.now()
        
        while current_time <= end_time:
            # Round to nearest 5-minute mark
            minutes = current_time.minute
            rounded_minutes = (minutes // 5) * 5
            target_time = current_time.replace(minute=rounded_minutes, second=0, microsecond=0)
            
            for symbol in symbols:
                ensure_technical_placeholders(cursor, symbol, target_time)
            
            current_time += timedelta(minutes=5)
        
        conn.commit()
        
        # Now calculate real indicators
        return calculate_indicators(backfill_days)
        
    finally:
        cursor.close()
        conn.close()
```

#### Enhanced Onchain Collector
```python
# services/onchain-collection/onchain_collector.py

def ensure_onchain_placeholders(cursor, symbol, target_date):
    """Create placeholder onchain records"""
    
    # Get the full field list from the enhanced collector
    onchain_fields = [
        'active_addresses_24h', 'transaction_count_24h', 'exchange_net_flow_24h',
        'price_volatility_7d', 'market_cap_realized', 'mvrv_ratio',
        # ... all 46-50 fields from enhanced collector
    ]
    
    # Create placeholder with all fields set to NULL and 0% completeness
    field_placeholders = ', '.join(['NULL'] * len(onchain_fields))
    field_names = ', '.join(onchain_fields)
    
    try:
        cursor.execute(f"""
            INSERT IGNORE INTO crypto_onchain_data
            (symbol, data_date, {field_names}, data_completeness_percentage, data_source, created_at)
            VALUES (%s, %s, {field_placeholders}, 0.0, 'placeholder_auto', NOW())
        """, (symbol, target_date))
        
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.debug(f"Error creating onchain placeholder for {symbol}: {e}")
        return False
```

### B. Centralized Placeholder Manager Service

```python
# services/placeholder-manager/placeholder_manager.py

class PlaceholderManager:
    """Centralized service for managing placeholder records across all collectors"""
    
    def __init__(self):
        self.db_config = get_db_config()
        
    def ensure_comprehensive_placeholders(self):
        """Ensure all expected placeholder records exist across all collectors"""
        
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            # 1. Ensure macro placeholders for last 7 days
            self.ensure_macro_placeholders(cursor, days=7)
            
            # 2. Ensure technical placeholders for last 24 hours (5-min intervals)
            self.ensure_technical_placeholders(cursor, hours=24)
            
            # 3. Ensure onchain placeholders for last 30 days
            self.ensure_onchain_placeholders(cursor, days=30)
            
            # 4. Ensure sentiment placeholders for last 7 days
            self.ensure_sentiment_placeholders(cursor, days=7)
            
            conn.commit()
            
        finally:
            cursor.close()
            conn.close()
    
    def detect_and_fill_gaps(self):
        """Detect missing placeholder records and create them"""
        
        # Check for gaps in expected data collection
        gaps = self.detect_collection_gaps()
        
        for gap in gaps:
            self.create_placeholder_for_gap(gap)
    
    def get_completeness_summary(self):
        """Get system-wide completeness summary"""
        
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get completeness by collector type
            cursor.execute("""
                SELECT 
                    'macro' as collector_type,
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_completeness_percentage > 0 THEN 1 ELSE 0 END) as filled_records,
                    AVG(data_completeness_percentage) as avg_completeness
                FROM macro_indicators 
                WHERE indicator_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                
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
                WHERE data_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            
            return cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()
```

### C. Integration with Existing Collectors

#### Update Kubernetes Deployments

```yaml
# k8s/collectors/collector-configmaps.yaml

# Add to macro collector
- name: ENSURE_PLACEHOLDERS
  value: "true"
- name: PLACEHOLDER_LOOKBACK_DAYS
  value: "7"

# Add to technical collector  
- name: ENSURE_PLACEHOLDERS
  value: "true"
- name: PLACEHOLDER_LOOKBACK_HOURS
  value: "24"

# Add to onchain collector
- name: ENSURE_PLACEHOLDERS
  value: "true" 
- name: PLACEHOLDER_LOOKBACK_DAYS
  value: "30"
```

#### Deploy Placeholder Manager Service

```yaml
# k8s/placeholder-manager/placeholder-manager-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: placeholder-manager
  namespace: crypto-data-collection
spec:
  replicas: 1
  selector:
    matchLabels:
      app: placeholder-manager
  template:
    metadata:
      labels:
        app: placeholder-manager
    spec:
      containers:
      - name: placeholder-manager
        image: python:3.11-slim
        command: ["python", "/app/placeholder_manager.py"]
        env:
        - name: DB_HOST
          value: "127.0.0.1"
        - name: SCHEDULE_INTERVAL_HOURS
          value: "1"
        volumeMounts:
        - name: placeholder-manager-code
          mountPath: /app
      volumes:
      - name: placeholder-manager-code
        configMap:
          name: placeholder-manager-config

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: placeholder-manager-cron
spec:
  schedule: "0 * * * *"  # Every hour
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: placeholder-manager
            image: python:3.11-slim
            command: ["python", "/app/placeholder_manager.py", "--ensure-placeholders"]
```

## Benefits of This Approach

### 1. **Proactive Gap Management**
- Create expected records before collection attempts
- Immediate visibility into what should exist vs what's missing
- Prevents "unknown unknowns" in data collection

### 2. **Enhanced Completeness Tracking**
- Every expected data point has a record (even if 0% complete)
- Completeness percentages become truly meaningful
- Clear distinction between "no data expected" vs "data missing"

### 3. **Improved Backfill Prioritization**
```sql
-- Find most critical gaps for backfill
SELECT 
    symbol,
    DATE(data_date) as missing_date,
    COUNT(*) as missing_fields,
    AVG(data_completeness_percentage) as avg_completeness
FROM crypto_onchain_data 
WHERE data_completeness_percentage < 50  -- Less than 50% complete
GROUP BY symbol, DATE(data_date)
ORDER BY avg_completeness ASC, missing_date DESC
LIMIT 100;
```

### 4. **Real-time Monitoring**
- Alert when placeholders remain unfilled beyond expected timeframes
- Track collection success rates more accurately
- Identify failing collectors immediately

## Implementation Timeline

### Phase 1: Core Integration (1-2 days)
1. Update macro collector with placeholder creation
2. Update technical calculator with placeholder creation  
3. Test with existing enhanced onchain collector

### Phase 2: Centralized Manager (2-3 days)
1. Create placeholder manager service
2. Deploy as Kubernetes CronJob
3. Integrate with monitoring and alerting

### Phase 3: Optimization (1 day)
1. Performance tuning for large placeholder volumes
2. Cleanup mechanisms for old placeholders
3. Advanced gap detection algorithms

## Expected Impact

- **Completeness Visibility**: 100% coverage of expected vs actual data points
- **Monitoring Quality**: Real-time alerts on collection failures  
- **Backfill Efficiency**: Focus on filling known gaps rather than discovering them
- **Data Quality**: Comprehensive tracking of collection success rates

This approach combines the benefits of distributed placeholder creation (fast, service-aware) with centralized management (consistency, global view) to create a robust system for automatic placeholder record management.