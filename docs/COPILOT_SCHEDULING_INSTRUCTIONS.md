# 📅 Collector Scheduling & Configuration Instructions

## 🎯 CRITICAL RULE: ALWAYS USE CENTRALIZED CONFIGURATION

**ALL collectors MUST reference centralized configuration for:**
- ✅ Database connections: `shared/database_config.py`
- ✅ Table names: `shared/table_config.py`  
- ✅ Scheduling frequencies: `shared/scheduling_config.py`

## 📋 CENTRALIZED SCHEDULING SYSTEM

### **📊 Current Collector Schedules**

| Collector | Frequency | Gap Tolerance | Auto-Backfill | Priority |
|-----------|-----------|---------------|----------------|----------|
| **Onchain** | 6 hours | 8 hours | ✅ Yes | Medium |
| **Technical** | 5 minutes | 15 minutes | ✅ Yes | High |
| **Macro** | 1 hour | 2 hours | ✅ Yes | Medium |
| **News** | 15 minutes | 1 hour | ✅ Yes | Medium |
| **OHLC** | Daily 2AM | 26 hours | ✅ Yes | High |
| **Sentiment** | 15 minutes | 1 hour | ✅ Yes | Medium |
| **Price** | 5 minutes | 15 minutes | ✅ Yes | Critical |

### **🔧 Implementation Pattern for New Collectors**

```python
#!/usr/bin/env python3
"""
New Collector Template - ALWAYS use this pattern
"""

import os
import sys
import logging
import schedule
from datetime import datetime, timedelta

# ✅ REQUIRED: Import centralized configurations
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.database_config import get_db_connection
    from shared.table_config import get_table_name, get_collector_config
    from shared.scheduling_config import (
        get_collector_schedule, 
        create_schedule_for_collector,
        get_gap_tolerance,
        should_auto_backfill
    )
except ImportError as e:
    logging.error(f"Failed to import centralized config: {e}")
    # Use fallback values but log the issue
    logging.warning("Using fallback configuration - UPDATE REQUIRED")

def collect_data():
    \"\"\"Main collection function\"\"\"
    # ✅ Use centralized database connection
    connection = get_db_connection()
    
    # ✅ Use centralized table configuration
    table_config = get_collector_config('your_collector_name')
    primary_table = table_config['primary_table']
    
    # Your collection logic here
    pass

def check_for_gaps():
    \"\"\"Gap detection using centralized config\"\"\"
    config = get_collector_schedule('your_collector_name')
    gap_tolerance = config['gap_tolerance_hours']
    
    # Check for gaps and trigger backfill if needed
    if should_auto_backfill('your_collector_name'):
        # Trigger backfill
        pass

def main():
    \"\"\"Main function with centralized scheduling\"\"\"
    logger = logging.getLogger(__name__)
    
    # ✅ Use centralized scheduling
    if create_schedule_for_collector:
        try:
            create_schedule_for_collector('your_collector_name', schedule, collect_data)
            logger.info("✅ Using centralized scheduling configuration")
        except Exception as e:
            logger.warning(f"Centralized config failed, using fallback: {e}")
            # Your fallback schedule here
            schedule.every(1).hours.do(collect_data)
    else:
        # Fallback schedule
        schedule.every(1).hours.do(collect_data)
    
    # Initial collection
    collect_data()
    
    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
```

## 🔄 GAP MONITORING & AUTO-BACKFILL

### **Gap Detection Pattern**
```python
def detect_gaps():
    \"\"\"Standard gap detection using centralized config\"\"\"
    config = get_collector_schedule('collector_name')
    
    # Get last record time
    last_record_time = get_last_record_timestamp()
    gap_hours = (datetime.now() - last_record_time).total_seconds() / 3600
    
    # Check against centralized tolerance
    if gap_hours > config['gap_tolerance_hours']:
        logger.warning(f"Gap detected: {gap_hours:.2f} hours")
        
        if config['auto_backfill']:
            trigger_backfill(gap_hours)
```

### **Auto-Backfill Implementation**
```python
def trigger_backfill(gap_hours):
    \"\"\"Trigger backfill using centralized configuration\"\"\"
    config = get_collector_schedule('collector_name')
    max_days = config['max_backfill_days']
    
    # Limit backfill to max allowed days
    backfill_days = min(int(gap_hours / 24) + 1, max_days)
    
    logger.info(f"Starting backfill for {backfill_days} days")
    # Execute backfill logic
```

## 📐 KUBERNETES CONFIGMAP INTEGRATION

### **ConfigMap Pattern for Collectors**
```yaml
# Always reference centralized scheduling
apiVersion: v1
kind: ConfigMap
metadata:
  name: collector-name-code
  namespace: crypto-data-collection
data:
  collector.py: |
    #!/usr/bin/env python3
    
    # Import centralized configurations
    from shared.scheduling_config import get_collector_schedule
    from shared.database_config import get_db_connection
    from shared.table_config import get_table_name
    
    def main():
        # Use centralized config for scheduling
        config = get_collector_schedule('collector_name')
        
        if config['schedule_type'] == 'minutes':
            schedule.every(config['schedule_value']).minutes.do(collect_data)
        elif config['schedule_type'] == 'hours':
            schedule.every(config['schedule_value']).hours.do(collect_data)
        elif config['schedule_type'] == 'daily':
            schedule.every().day.at(config['schedule_value']).do(collect_data)
```

## 🌍 ENVIRONMENT VARIABLE OVERRIDES

### **Environment Configuration**
```bash
# Override any collector schedule
export ONCHAIN_FREQUENCY_HOURS=8
export TECHNICAL_FREQUENCY_MINUTES=10
export MACRO_AUTO_BACKFILL=false
export NEWS_GAP_TOLERANCE_HOURS=2
```

### **Environment Integration**
```python
# Centralized config automatically handles environment overrides
config = get_collector_schedule('onchain')
# If ONCHAIN_FREQUENCY_HOURS=8 is set, config['frequency_hours'] = 8.0
```

## 🔍 DEBUGGING & VALIDATION

### **Configuration Validation**
```python
# Always validate configuration before deploying
from shared.scheduling_config import validate_all_configs

validations = validate_all_configs()
for collector, validation in validations.items():
    if not validation['valid']:
        logger.error(f"Invalid config for {collector}: {validation['errors']}")
    if validation['warnings']:
        logger.warning(f"Warnings for {collector}: {validation['warnings']}")
```

### **Health Check Integration**
```python
def health_check():
    \"\"\"Health check including configuration validation\"\"\"
    try:
        config = get_collector_schedule('collector_name')
        validation = validate_collector_config('collector_name')
        
        return {
            "status": "healthy" if validation['valid'] else "unhealthy",
            "config": config,
            "validation": validation,
            "last_collection": get_last_collection_time(),
            "next_collection": get_next_collection_time()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

## 📊 RATE LIMITING INTEGRATION

### **API Rate Limiting**
```python
from shared.scheduling_config import get_rate_limit_config, get_api_delay

# Get rate limiting for specific API
rate_config = get_rate_limit_config('coingecko_premium')
delay = get_api_delay('coingecko_premium')

# Apply rate limiting in your collector
time.sleep(delay)
```

## 🚀 DEPLOYMENT CHECKLIST

### **Before Deploying New Collector:**
1. ✅ Uses `shared/database_config.py` for DB connections
2. ✅ Uses `shared/table_config.py` for table names
3. ✅ Uses `shared/scheduling_config.py` for frequencies
4. ✅ Implements gap detection with centralized tolerance
5. ✅ Includes auto-backfill with centralized limits
6. ✅ Has environment variable overrides
7. ✅ Includes configuration validation
8. ✅ Implements health checks
9. ✅ Uses appropriate rate limiting
10. ✅ Follows the standard template pattern

### **Configuration Updates:**
1. ✅ Add collector to `COLLECTOR_SCHEDULES` in `scheduling_config.py`
2. ✅ Add table mappings to `table_config.py` if needed
3. ✅ Update Kubernetes ConfigMaps to reference centralized config
4. ✅ Test configuration validation
5. ✅ Document any new environment variables

## ⚡ PERFORMANCE OPTIMIZATION

### **High-Frequency Collectors (< 10 minutes)**
- Use priority queues
- Implement batch processing
- Monitor rate limits closely
- Consider database connection pooling

### **Low-Frequency Collectors (> 1 hour)**
- Focus on data completeness
- Implement comprehensive backfill
- Use longer gap tolerances
- Optimize for accuracy over speed

## 🔧 TROUBLESHOOTING

### **Common Issues:**
1. **ImportError on centralized config**: Check Python path and file locations
2. **Invalid schedule type**: Verify `schedule_type` in `COLLECTOR_SCHEDULES`
3. **Environment overrides not working**: Check environment variable naming convention
4. **Rate limiting errors**: Verify API configuration in `RATE_LIMITS`
5. **Gap detection failing**: Check database connectivity and table existence

### **Debug Commands:**
```python
# Validate all configurations
python shared/scheduling_config.py

# Check specific collector
from shared.scheduling_config import validate_collector_config
result = validate_collector_config('collector_name')
print(result)

# Test database connectivity
from shared.database_config import test_db_connection
print(test_db_connection())
```

---

## 🎯 SUMMARY

**ALWAYS REMEMBER:**
1. **Use centralized configurations** - Never hardcode schedules, tables, or DB configs
2. **Implement gap monitoring** - Every collector needs gap detection
3. **Enable auto-backfill** - Use centralized limits and triggers
4. **Include health checks** - Monitor configuration validity
5. **Test thoroughly** - Validate configs before deployment
6. **Document changes** - Update this guide when adding new patterns

**The centralized configuration system ensures consistency, maintainability, and easy management across all collectors.**

---

*Last Updated: November 4, 2025*
*Configuration Files: `shared/scheduling_config.py`, `shared/database_config.py`, `shared/table_config.py`*