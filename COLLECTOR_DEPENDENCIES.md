# Collector Dependencies Analysis

## News Collector (enhanced_news_collector_template.py)

### Direct Imports:
- **asyncio** - stdlib
- **aiohttp** - HTTP client for async requests
- **feedparser** - RSS feed parsing
- **re, hashlib, time** - stdlib
- **datetime, timezone, timedelta** - stdlib
- **typing** - stdlib
- **mysql.connector** - MySQL database
- **base_collector_template** - internal

### From base_collector_template.py:
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **prometheus_client** - Metrics
- **structlog** - Structured logging
- **aiohttp** - Already listed

### Minimal Requirements (news-collector):
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
aiohttp>=3.9.0
mysql-connector-python>=8.2.0
feedparser>=6.0.10
prometheus-client>=0.19.0
structlog>=24.1.0
```

**Expected size**: ~200-250MB (base Python + these packages)

---

## To Analyze Next:
1. Sentiment ML collector
2. Technical calculator
3. OHLC collector
4. Materialized updater
5. Prices service
6. News collector (sub)
7. Onchain collector
8. Technical indicators
9. Macro collector
10. Derivatives collector
11. ML Market collector
