# API Integration Guide - Enhanced Onchain Data Collector

## 🚀 Overview

This guide provides detailed documentation for integrating with all external APIs used by the Enhanced Onchain Data Collector. Each API is documented with authentication, endpoints, rate limits, error handling, and implementation examples.

---

## 🔑 API Authentication & Keys

### **CoinGecko Premium API**
```python
API_KEY = "CG-94NCcVD2euxaGTZe94bS2oYz"
BASE_URL = "https://pro-api.coingecko.com/api/v3"
TIER = "Premium"
RATE_LIMIT = "10 requests/second"
MONTHLY_QUOTA = "500,000 requests"
```

**Headers Required**:
```python
headers = {
    "x-cg-pro-api-key": API_KEY,
    "Content-Type": "application/json"
}
```

### **DeFiLlama API (Public)**
```python
BASE_URL = "https://api.llama.fi"
RATE_LIMIT = "2 requests/second"
AUTHENTICATION = "None (Public API)"
```

### **Blockchain.info API (Public)**
```python
BASE_URL = "https://api.blockchain.info"
RATE_LIMIT = "Conservative 2-3 requests/second"
AUTHENTICATION = "None (Public API)"
```

---

## 📡 API Endpoints & Data Mapping

### **1. CoinGecko Premium API**

#### **Primary Endpoint: Coin Details**
```
GET /coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=true&sparkline=false
```

**Response Mapping**:
```python
# Market Data
market_data = response["market_data"]
circulating_supply = market_data["circulating_supply"]
total_supply = market_data["total_supply"]
max_supply = market_data["max_supply"]

# Developer Data
developer_data = response["developer_data"]
github_commits_30d = developer_data["commit_count_4_weeks"]

# Community Data (moved to sentiment table)
community_data = response["community_data"]
```

#### **Rate Limiting Implementation**:
```python
import time
from typing import Optional

class CoinGeckoRateLimit:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 0.1  # 10 requests/second = 0.1s between requests
    
    async def wait_if_needed(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()
```

### **2. DeFiLlama API**

#### **Chains Endpoint: TVL by Chain**
```
GET /v2/chains
```

**Response Processing**:
```python
def process_defilama_chains(response_data):
    chains_map = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH', 
        'avalanche': 'AVAX',
        'polygon': 'MATIC',
        'solana': 'SOL',
        'cardano': 'ADA'
    }
    
    tvl_data = {}
    for chain in response_data:
        chain_name = chain.get('name', '').lower()
        if chain_name in chains_map:
            symbol = chains_map[chain_name]
            tvl_data[symbol] = {
                'total_value_locked': chain.get('tvl', 0),
                'defi_protocols_count': len(chain.get('protocols', []))
            }
    return tvl_data
```

#### **Protocols Endpoint: Protocol Counting**
```
GET /protocols
```

**Protocol Counting Logic**:
```python
def count_protocols_by_chain(protocols_data, min_tvl=100000):
    """Count active protocols by chain with minimum TVL threshold"""
    chain_counts = {}
    
    for protocol in protocols_data:
        tvl = protocol.get('tvl', 0)
        if tvl < min_tvl:
            continue
            
        chains = protocol.get('chains', [])
        for chain in chains:
            chain = chain.lower()
            if chain not in chain_counts:
                chain_counts[chain] = 0
            chain_counts[chain] += 1
    
    return chain_counts
```

### **3. Blockchain.info API**

#### **Bitcoin Network Stats**
```
GET /stats
```

**Data Extraction**:
```python
async def get_bitcoin_network_data(session):
    """Get Bitcoin-specific network metrics"""
    try:
        async with session.get(f"{BLOCKCHAIN_INFO_URL}/stats") as response:
            if response.status == 200:
                data = await response.json()
                return {
                    'hash_rate': data.get('hash_rate', 0) / 1e12,  # Convert to TH/s
                    'difficulty': data.get('difficulty', 0),
                    'block_height': data.get('n_blocks_total', 0),
                    'transaction_count': data.get('n_tx', 0)
                }
    except Exception as e:
        logger.warning(f"Failed to fetch Bitcoin data: {e}")
    return None
```

### **4. Network-Specific APIs**

#### **Ethereum Block Height (Etherscan)**
```
GET https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey=YourApiKeyToken
```

**Implementation**:
```python
async def get_ethereum_block_height(session):
    """Get current Ethereum block height"""
    try:
        params = {
            'module': 'proxy',
            'action': 'eth_blockNumber'
        }
        async with session.get("https://api.etherscan.io/api", params=params) as response:
            if response.status == 200:
                data = await response.json()
                hex_block = data.get('result', '0x0')
                return int(hex_block, 16)
    except Exception as e:
        logger.warning(f"Failed to fetch Ethereum block height: {e}")
    return None
```

---

## ⚠️ Error Handling & Resilience

### **HTTP Error Handling**
```python
async def safe_api_request(session, url, headers=None, params=None, timeout=30):
    """Make a safe API request with comprehensive error handling"""
    try:
        async with session.get(url, headers=headers, params=params, timeout=timeout) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                # Rate limit exceeded
                retry_after = response.headers.get('Retry-After', 60)
                logger.warning(f"Rate limit exceeded, waiting {retry_after}s")
                await asyncio.sleep(int(retry_after))
                return None
            elif response.status >= 500:
                # Server error - temporary issue
                logger.warning(f"Server error {response.status}, will retry")
                return None
            else:
                # Client error - permanent issue
                logger.error(f"Client error {response.status}: {await response.text()}")
                return None
    except asyncio.TimeoutError:
        logger.warning(f"Request timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"Request failed for {url}: {e}")
        return None
```

### **Fallback Data Strategies**

#### **Estimation Functions**
```python
def estimate_network_activity(symbol, market_cap_rank, network_type):
    """Estimate network activity when real data unavailable"""
    
    # Base transaction estimates by network type
    base_estimates = {
        'pow': {'btc': 300000, 'ltc': 50000, 'etc': 15000},
        'pos': {'eth': 1200000, 'ada': 150000, 'sol': 800000, 'avax': 200000}
    }
    
    # Activity multipliers by market cap rank
    rank_multipliers = {
        (1, 5): 1.0,      # Top 5: full activity
        (6, 20): 0.7,     # Top 20: 70% activity
        (21, 50): 0.4,    # Top 50: 40% activity
        (51, 100): 0.2,   # Top 100: 20% activity
        (101, float('inf')): 0.1  # Others: 10% activity
    }
    
    # Calculate estimates
    base_tx = base_estimates.get(network_type, {}).get(symbol.lower(), 100000)
    
    for (min_rank, max_rank), multiplier in rank_multipliers.items():
        if min_rank <= market_cap_rank <= max_rank:
            return int(base_tx * multiplier)
    
    return 10000  # Fallback minimum
```

#### **Supply Inflation Rates**
```python
SUPPLY_INFLATION_RATES = {
    'BTC': 0.0065,   # ~0.65% (decreasing due to halvings)
    'ETH': -0.001,   # ~-0.1% (deflationary post-merge)
    'ADA': 0.003,    # ~0.3% (PoS rewards)
    'DOT': 0.10,     # ~10% (high inflation)
    'SOL': 0.08,     # ~8% (decreasing schedule)
    'AVAX': 0.02,    # ~2% (moderate inflation)
    'MATIC': 0.05,   # ~5% (validator rewards)
    'ATOM': 0.07,    # ~7% (Cosmos staking)
    'ALGO': 0.05,    # ~5% (participation rewards)
    'XTZ': 0.058     # ~5.8% (baking rewards)
}
```

---

## 📊 Data Quality & Validation

### **Quality Scoring System**
```python
def calculate_data_quality_score(data_sources, has_estimates=False):
    """Calculate data quality score based on sources and estimation usage"""
    
    source_scores = {
        'coingecko_premium': 0.95,
        'coingecko_free': 0.8,
        'defilama': 0.9,
        'blockchain_info': 0.9,
        'network_api': 0.85,
        'estimates': 0.6
    }
    
    # Base score from primary source
    if 'coingecko_premium' in data_sources:
        base_score = source_scores['coingecko_premium']
    elif 'coingecko_free' in data_sources:
        base_score = source_scores['coingecko_free']
    else:
        base_score = 0.7
    
    # Multi-source bonus
    if len(data_sources) > 2:
        base_score += 0.05
    
    # Estimation penalty
    if has_estimates:
        base_score -= 0.1
    
    return min(max(base_score, 0.0), 1.0)
```

### **Data Validation Rules**
```python
def validate_crypto_data(data):
    """Validate collected cryptocurrency data for consistency"""
    
    errors = []
    
    # Supply validation
    circulating = data.get('circulating_supply', 0)
    total = data.get('total_supply', 0)
    max_supply = data.get('max_supply')
    
    if circulating > total:
        errors.append("Circulating supply cannot exceed total supply")
    
    if max_supply and total > max_supply:
        errors.append("Total supply cannot exceed max supply")
    
    # Network activity validation
    tx_count = data.get('transaction_count', 0)
    tx_volume = data.get('transaction_volume', 0)
    
    if tx_count < 0 or tx_volume < 0:
        errors.append("Transaction metrics cannot be negative")
    
    # Staking validation for PoS networks
    staked_pct = data.get('staked_percentage', 0)
    if staked_pct > 100:
        errors.append("Staked percentage cannot exceed 100%")
    
    # DeFi validation
    tvl = data.get('total_value_locked', 0)
    protocols = data.get('defi_protocols_count', 0)
    
    if tvl > 0 and protocols == 0:
        errors.append("TVL exists but no protocols counted")
    
    return errors
```

---

## 🔄 Retry Logic & Circuit Breakers

### **Exponential Backoff**
```python
import random
import asyncio

async def retry_with_backoff(func, max_retries=3, base_delay=1, max_delay=60):
    """Execute function with exponential backoff retry logic"""
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Max retries exceeded: {e}")
                raise
            
            # Calculate backoff delay with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0.1, 0.3) * delay
            total_delay = delay + jitter
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.1f}s")
            await asyncio.sleep(total_delay)
```

### **Circuit Breaker Pattern**
```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## 📈 Performance Monitoring

### **API Response Time Tracking**
```python
import time
from collections import defaultdict

class APIMetrics:
    def __init__(self):
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
    
    async def track_request(self, api_name, request_func):
        start_time = time.time()
        try:
            result = await request_func()
            self.success_counts[api_name] += 1
            return result
        except Exception as e:
            self.error_counts[api_name] += 1
            raise
        finally:
            response_time = time.time() - start_time
            self.response_times[api_name].append(response_time)
            
            # Keep only last 100 measurements
            if len(self.response_times[api_name]) > 100:
                self.response_times[api_name] = self.response_times[api_name][-100:]
    
    def get_stats(self, api_name):
        times = self.response_times[api_name]
        if not times:
            return None
        
        return {
            'avg_response_time': sum(times) / len(times),
            'max_response_time': max(times),
            'min_response_time': min(times),
            'success_rate': self.success_counts[api_name] / (
                self.success_counts[api_name] + self.error_counts[api_name]
            ),
            'total_requests': self.success_counts[api_name] + self.error_counts[api_name]
        }
```

---

## 🚀 Implementation Example

### **Complete API Integration**
```python
import asyncio
import aiohttp
from datetime import datetime

class EnhancedOnchainAPIClient:
    def __init__(self):
        self.coingecko_rate_limit = CoinGeckoRateLimit()
        self.defilama_circuit_breaker = CircuitBreaker()
        self.metrics = APIMetrics()
    
    async def collect_all_data(self, symbol, coin_id):
        """Collect comprehensive onchain data from all APIs"""
        
        async with aiohttp.ClientSession() as session:
            # Parallel API calls with error handling
            tasks = [
                self._safe_coingecko_request(session, coin_id),
                self._safe_defilama_request(session),
                self._safe_blockchain_request(session, symbol),
                self._safe_network_request(session, symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results with fallbacks
            final_data = self._merge_api_results(symbol, *results)
            
            # Calculate quality score
            final_data['data_quality_score'] = self._calculate_quality_score(final_data)
            
            return final_data
    
    async def _safe_coingecko_request(self, session, coin_id):
        await self.coingecko_rate_limit.wait_if_needed()
        return await self.metrics.track_request(
            'coingecko',
            lambda: self._fetch_coingecko_data(session, coin_id)
        )
    
    # ... Additional implementation methods
```

---

## 📋 API Monitoring Checklist

### **Daily Monitoring Tasks**
- [ ] Check API response times and success rates
- [ ] Verify rate limit compliance
- [ ] Monitor data quality scores
- [ ] Review error logs for patterns
- [ ] Validate data consistency across sources

### **Weekly Reviews**
- [ ] Analyze API performance trends
- [ ] Update fallback estimations if needed
- [ ] Review circuit breaker triggers
- [ ] Test failover mechanisms
- [ ] Update API documentation

### **Monthly Assessments**
- [ ] API cost analysis and optimization
- [ ] Evaluate new data sources
- [ ] Update authentication tokens if needed
- [ ] Performance benchmark comparisons
- [ ] Data quality improvement initiatives

---

*Last Updated: November 10, 2025*  
*Version: 2.0 - Multi-Source API Integration*