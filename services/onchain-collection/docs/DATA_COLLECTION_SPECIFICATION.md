# Enhanced Onchain Data Collection - Complete Specification

## 📋 Overview

This document provides a comprehensive specification of all data fields collected by the Enhanced Onchain Data Collector, including data sources, collection methods, purposes, and applicability across different blockchain networks.

**Collection Coverage**: 25/29 database schema fields (86.2%)  
**Data Sources**: CoinGecko Premium, DeFiLlama, Blockchain.info, Etherscan, Network APIs  
**Update Frequency**: 15-minute intervals for optimal signal detection  
**Architecture**: Database-driven symbol management, multi-source real data integration

---

## 🗄️ Database Schema & Field Specification

### **Core Identification Fields**

| Field | Type | Source | Purpose | Coverage |
|-------|------|--------|---------|----------|
| `id` | BIGINT AUTO_INCREMENT | Database | Primary key for record identification | 100% (Auto-generated) |
| `symbol` | VARCHAR(100) | crypto_assets table | Asset symbol (BTC, ETH, etc.) | 100% |
| `coin_id` | VARCHAR(150) | CoinGecko API | CoinGecko unique identifier for API calls | 100% |
| `timestamp_iso` | DATETIME(6) | System | Collection timestamp in ISO format | 100% |
| `collected_at` | TIMESTAMP | Database | Record insertion timestamp | 100% (Auto-generated) |

### **Network Activity Metrics**

| Field | Type | Source | Purpose | Coverage | Notes |
|-------|------|--------|---------|----------|-------|
| `active_addresses` | BIGINT | CoinGecko + Estimates | Daily active network addresses | 100% | Real data for major chains, estimates for others |
| `transaction_count` | BIGINT | CoinGecko + Estimates | 24-hour transaction count | 100% | Network activity indicator |
| `transaction_volume` | DECIMAL(25,8) | CoinGecko + Calculations | USD value of onchain transactions | 100% | Derived from trading volume ratios |
| `block_height` | BIGINT | Blockchain APIs + Estimates | Current blockchain height | 95% | Real for BTC/ETH, estimated for others |
| `block_time_seconds` | DECIMAL(10,2) | Network Constants | Average block production time | 100% | Known values per network |

### **Blockchain Security Metrics (PoW Only)**

| Field | Type | Source | Purpose | Coverage | Applicability |
|-------|------|--------|---------|----------|---------------|
| `hash_rate` | DECIMAL(25,8) | Blockchain.info | Network hash rate (TH/s) | PoW Only | Bitcoin, Litecoin, etc. |
| `difficulty` | DECIMAL(25,8) | Blockchain.info | Mining difficulty | PoW Only | Bitcoin, Ethereum Classic, etc. |

**Note**: These fields are intentionally NULL for Proof-of-Stake networks (ETH, ADA, SOL, AVAX) as they don't apply to PoS consensus mechanisms.

### **Supply Economics**

| Field | Type | Source | Purpose | Coverage | Calculation Method |
|-------|------|--------|---------|----------|-------------------|
| `circulating_supply` | DECIMAL(25,8) | CoinGecko | Coins currently in circulation | 100% | Direct from CoinGecko market data |
| `total_supply` | DECIMAL(25,8) | CoinGecko | Total coins minted | 100% | Direct from CoinGecko market data |
| `max_supply` | DECIMAL(25,8) | CoinGecko | Maximum possible supply | 90% | NULL for inflationary tokens |
| `supply_inflation_rate` | DECIMAL(10,4) | Network Constants | Annual supply inflation % | 85% | Known rates per network |

**Supply Inflation Rates by Network**:
- Bitcoin: 0.65% (halving schedule)
- Ethereum: -0.10% (post-merge deflationary)
- Cardano: 0.30% (PoS rewards)
- Polkadot: 10.0% (high inflation)
- Solana: 8.0% (decreasing schedule)
- Avalanche: 2.0% (moderate inflation)
- Polygon: 5.0% (validator rewards)

### **Network Value Metrics**

| Field | Type | Source | Purpose | Coverage | Calculation |
|-------|------|--------|---------|----------|-------------|
| `network_value_to_transactions` | DECIMAL(20,8) | Calculated | NVT ratio for network valuation | 100% | Market Cap / Transaction Volume |
| `realized_cap` | DECIMAL(25,2) | Messari + Estimates | Value of coins at acquisition price | 90% | MVRV-based estimation |
| `mvrv_ratio` | DECIMAL(10,4) | Calculated | Market-to-Realized Value ratio | 100% | Market Cap / Realized Cap |
| `nvt_ratio` | DECIMAL(10,4) | Calculated | Network Value to Transactions | 100% | Alternative valuation metric |

### **Development Activity**

| Field | Type | Source | Purpose | Coverage | Measurement Period |
|-------|------|--------|---------|----------|-------------------|
| `github_commits_30d` | INT | CoinGecko Developer Data | Recent development activity | 95% | Last 30 days |
| `developer_activity_score` | DECIMAL(10,4) | Calculated | Normalized dev activity (0-1) | 95% | Commits / 100 (capped at 1.0) |

### **Staking Metrics (PoS Networks)**

| Field | Type | Source | Purpose | Coverage | Applicability |
|-------|------|--------|---------|----------|---------------|
| `staking_yield` | DECIMAL(10,4) | Network Data + Constants | Annual staking reward % | PoS Only | Cardano, Polkadot, Solana, etc. |
| `staked_percentage` | DECIMAL(10,4) | Network Data + Constants | % of supply staked | PoS Only | Network security indicator |
| `validator_count` | INT | Network Data + Constants | Active validator count | PoS Only | Decentralization metric |

**Staking Data by Network**:
- Cardano (ADA): 4.5% yield, 72% staked, 3,000 pools
- Polkadot (DOT): 12.0% yield, 55% staked, 297 validators
- Solana (SOL): 6.8% yield, 75% staked, 1,400 validators
- Avalanche (AVAX): 9.2% yield, 65% staked, 1,200 validators
- Polygon (MATIC): 3.8% yield, 40% staked, 100 validators
- Ethereum (ETH): 3.2% yield, 22% staked, 900,000 validators

### **DeFi Ecosystem Metrics**

| Field | Type | Source | Purpose | Coverage | Update Method |
|-------|------|--------|---------|----------|---------------|
| `total_value_locked` | DECIMAL(25,2) | DeFiLlama API | Total USD value locked in DeFi | Smart Contract Platforms | Real-time via DeFiLlama |
| `defi_protocols_count` | INT | DeFiLlama API | Active DeFi protocols (>$100k TVL) | Smart Contract Platforms | Counted from protocol list |

**DeFi Platform Coverage**:
- Ethereum: ~$77B TVL, 1,010+ protocols
- Avalanche: ~$1.5B TVL, 271+ protocols
- Polygon: Protocol counting via chain analysis
- Binance Smart Chain: Full ecosystem coverage
- Solana: DeFi protocol integration
- Cardano: Growing DeFi ecosystem (~$270M TVL, 55 protocols)

### **Data Quality & Metadata**

| Field | Type | Source | Purpose | Coverage | Values |
|-------|------|--------|---------|----------|--------|
| `data_source` | VARCHAR(100) | System | Comma-separated list of data sources | 100% | "coingecko,defilama,network-api" |
| `data_quality_score` | DECIMAL(3,2) | Calculated | Data completeness score (0-1) | 100% | 0.95 (premium), 0.8 (free) |

---

## 🔌 Data Sources & APIs

### **Primary Sources**

#### **1. CoinGecko Premium API**
- **Endpoint**: `https://pro-api.coingecko.com/api/v3/coins/{coin_id}`
- **API Key**: `CG-94NCcVD2euxaGTZe94bS2oYz` (Premium)
- **Rate Limit**: 10 requests/second (Premium tier)
- **Data Provided**:
  - Market data (prices, market cap, volume)
  - Supply metrics (circulating, total, max supply)
  - Developer activity (GitHub commits, stars, forks)
  - Community data (social metrics - moved to sentiment table)

#### **2. DeFiLlama API**
- **Endpoint**: `https://api.llama.fi/v2/chains`, `https://api.llama.fi/protocols`
- **Rate Limit**: 2 requests/second (Public API)
- **Data Provided**:
  - Total Value Locked (TVL) by chain
  - Active protocol counts
  - DeFi ecosystem health metrics
- **Chain Mappings**:
  - ETH → ethereum
  - AVAX → avalanche
  - MATIC → polygon
  - BNB → bsc
  - SOL → solana
  - ADA → cardano

#### **3. Blockchain.info API**
- **Endpoint**: `https://api.blockchain.info/stats`
- **Rate Limit**: Conservative (2-3 requests/second)
- **Data Provided** (Bitcoin only):
  - Hash rate (TH/s)
  - Network difficulty
  - Block height
  - Transaction statistics

#### **4. Etherscan API**
- **Endpoint**: `https://api.etherscan.io/api`
- **Rate Limit**: 5 requests/second (Free tier)
- **Data Provided** (Ethereum):
  - Block height
  - Network statistics
  - Transaction data

### **Fallback & Estimation Methods**

#### **Network Activity Estimates**
When real-time data is unavailable, estimates are calculated based on:
- Market cap tier classification
- Historical network patterns
- Network type (PoW vs PoS)
- Known network parameters

#### **Supply Inflation Calculations**
- Based on tokenomics documentation
- Validated against historical data
- Network-specific emission schedules
- Adjusted for governance changes

---

## 🎯 Data Purpose & Use Cases

### **Trading & Investment Analysis**
- **Network Activity**: Adoption and usage trends
- **Supply Metrics**: Scarcity and inflation analysis
- **DeFi Metrics**: Ecosystem growth and adoption
- **Development Activity**: Project health and progress

### **Risk Assessment**
- **Staking Metrics**: Network security and decentralization
- **Hash Rate/Difficulty**: PoW network security (Bitcoin)
- **Validator Count**: PoS network resilience
- **Data Quality Score**: Reliability assessment

### **Market Research**
- **Transaction Volume**: Network utilization
- **NVT/MVRV Ratios**: Valuation metrics
- **TVL Growth**: DeFi ecosystem expansion
- **Cross-chain Comparisons**: Competitive analysis

### **Academic & Research Applications**
- **Network Economics**: Supply and demand dynamics
- **Consensus Mechanism Studies**: PoW vs PoS comparison
- **Developer Ecosystem**: Open source contribution patterns
- **DeFi Innovation**: Protocol development trends

---

## ⚡ Collection Process & Frequency

### **Collection Schedule**
- **Frequency**: Every 15 minutes
- **Rationale**: Optimal for signal detection without overwhelming APIs
- **Peak Hours**: Consistent collection regardless of market conditions

### **Data Flow Pipeline**
1. **Symbol Retrieval**: Database-driven from `crypto_assets` table
2. **Multi-Source Collection**: Parallel API calls to all sources
3. **Data Validation**: Quality checks and null handling
4. **Data Merging**: Intelligent combination prioritizing real data
5. **Database Storage**: Upsert with conflict resolution
6. **Quality Scoring**: Assessment of data completeness

### **Error Handling & Resilience**
- **API Failures**: Graceful degradation to estimates
- **Rate Limiting**: Intelligent backoff and retry logic
- **Data Validation**: Sanity checks and outlier detection
- **Logging**: Comprehensive error tracking and monitoring

---

## 🔍 Data Quality & Validation

### **Quality Scoring Algorithm**
- **Premium Sources**: 0.95 base score
- **Free Sources**: 0.8 base score
- **Real vs Estimated**: -0.1 penalty for estimates
- **Multi-Source**: +0.05 bonus for data confirmation

### **Validation Rules**
- **Numeric Ranges**: Sanity checks for realistic values
- **Supply Logic**: Circulating ≤ Total ≤ Max supply
- **Network Consistency**: Block height monotonic increase
- **Cross-Reference**: Multi-source data comparison

### **Missing Data Handling**
- **Graceful Degradation**: Estimates when APIs fail
- **Null Values**: Preserved for inappropriate metrics (e.g., hash_rate for PoS)
- **Historical Context**: Previous values for validation
- **Documentation**: Clear indication of data source and quality

---

## 🔮 Future Enhancements

### **Planned Improvements**
- **Additional Networks**: Layer 2 solutions (Arbitrum, Optimism)
- **Enhanced Metrics**: MEV data, validator performance
- **Real-time Streams**: WebSocket integrations for faster updates
- **Machine Learning**: Anomaly detection and data quality ML

### **Research Opportunities**
- **Cross-chain Analytics**: Inter-network flow analysis
- **Governance Metrics**: DAO participation and voting
- **Environmental Impact**: Energy consumption tracking
- **Regulatory Compliance**: KYC/AML relevant metrics

---

## 📊 Data Dictionary Summary

| Category | Fields Collected | Coverage | Primary Sources |
|----------|------------------|----------|-----------------|
| **Core Identity** | 5 fields | 100% | Database, CoinGecko |
| **Network Activity** | 5 fields | 100% | CoinGecko, Blockchain APIs |
| **Security (PoW)** | 2 fields | PoW Only | Blockchain.info |
| **Supply Economics** | 4 fields | 90%+ | CoinGecko, Calculations |
| **Network Value** | 4 fields | 100% | Calculated Metrics |
| **Development** | 2 fields | 95% | CoinGecko GitHub Data |
| **Staking (PoS)** | 3 fields | PoS Only | Network Constants |
| **DeFi Ecosystem** | 2 fields | Smart Contract Platforms | DeFiLlama |
| **Data Quality** | 2 fields | 100% | System Generated |

**Total**: 29 database schema fields with 86.2% average coverage across all network types.

---

*Last Updated: November 10, 2025*  
*Version: 2.0 - Enhanced Multi-Source Integration*