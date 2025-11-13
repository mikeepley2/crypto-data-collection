# OHLC Service Consolidation Decision

## Summary
The OHLC collection service has been consolidated into a single comprehensive file: `enhanced_ohlc_collector.py`

## File Status

### ✅ KEEP: enhanced_ohlc_collector.py (25,835 lines)
**Complete production-ready OHLC collector with all functionality**
- Full FastAPI service with 7 endpoints (/health, /status, /metrics, /collect, /gap-check, /backfill, /ohlc-features)
- Volume data enhancement (fetches 24h volume from CoinGecko)
- Health scoring and monitoring
- Background task support
- Prometheus metrics integration
- Template compliance (100% matching derivatives/technical collector pattern)
- Can run in both API mode and scheduler mode
- Main entry point with argument parsing

### ❌ DEPRECATED: ohlc_service.py (28 lines - now deprecation notice)
**Redundant wrapper - functionality absorbed into enhanced_ohlc_collector.py**
- Was a thin wrapper around enhanced_ohlc_collector
- Provided no additional functionality
- Added unnecessary abstraction layer
- Now contains deprecation notice redirecting to enhanced_ohlc_collector.py

### ✅ KEEP: start_ohlc_service.sh
**Startup script correctly points to enhanced_ohlc_collector.py**
- Already configured to use enhanced_ohlc_collector.py
- Includes port checking and proper service startup

## Usage

### Start OHLC Service (FastAPI):
```bash
python enhanced_ohlc_collector.py --mode api --port 8002
```

### Start OHLC Service (Scheduled):
```bash
python enhanced_ohlc_collector.py --mode scheduler
```

### Using Startup Script:
```bash
./start_ohlc_service.sh 8002
```

## Features Confirmed Working
- ✅ OHLC data collection from CoinGecko Premium API
- ✅ Volume data enhancement (resolved 0% volume population issue)
- ✅ Database storage with ON DUPLICATE KEY UPDATE
- ✅ Rate limiting and error handling
- ✅ Health monitoring and scoring
- ✅ FastAPI endpoints for monitoring and control
- ✅ Template compliance with established patterns

## Consolidation Benefits
1. **Reduced Complexity**: Single file instead of wrapper + collector
2. **Maintenance**: Easier to maintain one comprehensive service
3. **Performance**: No extra abstraction layer overhead
4. **Clarity**: Clear single entry point for OHLC functionality
5. **Template Compliance**: Matches established collector patterns

## Recommendation
**Remove ohlc_service.py after confirming enhanced_ohlc_collector.py works in production**

The enhanced collector provides all functionality that was in the service wrapper, plus enhanced volume data collection and better template compliance.