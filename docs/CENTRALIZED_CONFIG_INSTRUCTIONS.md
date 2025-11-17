# 🎯 CENTRALIZED CONFIGURATION INSTRUCTIONS

## 📋 **MANDATORY REQUIREMENTS FOR ALL DEVELOPMENT**

**⚠️ CRITICAL**: All development, deployment, and operations MUST reference the centralized configuration system. No exceptions.

---

## 🏗️ **CENTRALIZED TABLE CONFIGURATION**

### **📍 Master Configuration File**: `shared/table_config.py`

**RULE**: All table references MUST use the centralized table registry.

```python
# ✅ CORRECT - Use centralized config
from shared.table_config import CRYPTO_TABLES, get_master_onchain_table

# Use master table constants
onchain_table = CRYPTO_TABLES["ONCHAIN_DATA"]  # "crypto_onchain_data"
assets_table = CRYPTO_TABLES["ASSETS"]         # "crypto_assets"

# Or use convenience functions
master_table = get_master_onchain_table()      # "crypto_onchain_data"
```

```python
# ❌ WRONG - Hard-coded table names
table_name = "crypto_onchain_data"              # DON'T DO THIS
table_name = "crypto_onchain_data_enhanced"     # DEPRECATED TABLE
```

### **🔍 Table Validation**

**RULE**: Always validate table names before use.

```python
from shared.table_config import validate_table_usage

# Validate before using any table
result = validate_table_usage("crypto_onchain_data")
if result["status"] != "approved":
    raise ValueError(f"Table not approved: {result}")
```

### **📊 Available Table Categories**

1. **Crypto Tables** (`CRYPTO_TABLES`)
   - `ASSETS`: `crypto_assets`
   - `ONCHAIN_DATA`: `crypto_onchain_data` (MASTER)
   - `PRICES`: `crypto_prices`
   - `NEWS`: `crypto_news`

2. **Technical Tables** (`TECHNICAL_TABLES`)
   - `INDICATORS`: `technical_indicators`
   - `BOLLINGER`: `bollinger_bands`
   - `OHLC`: `ohlc_data`

3. **ML Tables** (`ML_TABLES`)
   - `FEATURES`: `ml_features_materialized`
   - `SIGNALS`: `trading_signals`
   - `RECOMMENDATIONS`: `trade_recommendations`

4. **Market Tables** (`MARKET_TABLES`)
   - `MACRO`: `macro_indicators`
   - `SENTIMENT`: `sentiment_aggregation`
   - `VOLUME`: `volume_data`

5. **Operational Tables** (`OPERATIONAL_TABLES`)
   - `MONITORING`: `service_monitoring`
   - `BACKTEST`: `backtesting_results`
   - `PORTFOLIO`: `portfolio_optimizations`

---

## 🔧 **CENTRALIZED DATABASE CONFIGURATION**

### **📍 Master Configuration File**: `shared/database_config.py`

**RULE**: All database connections MUST use the centralized database configuration.

```python
# ✅ CORRECT - Use centralized database config
from shared.database_config import get_db_connection, get_db_config

# Get database connection
connection = get_db_connection()

# Get configuration for manual connection
config = get_db_config()
```

```python
# ❌ WRONG - Hard-coded database config
config = {
    'host': '172.22.32.1',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}
```

### **🌐 Environment Variables**

The centralized config uses these environment variables:

```bash
# Database configuration
DB_HOST=172.22.32.1
DB_PORT=3306
DB_USER=news_collector
DB_PASSWORD=99Rules!
DB_NAME=crypto_prices
DB_CONNECTION_TIMEOUT=30
DB_POOL_SIZE=10
```

### **🔍 Database Testing**

```python
from shared.database_config import test_db_connection

# Always test connectivity
if not test_db_connection():
    raise ConnectionError("Database connection failed")
```

---

## 🚀 **COLLECTOR CONFIGURATION**

### **📍 Collector Configuration**: `shared/table_config.py` → `COLLECTOR_TABLE_CONFIG`

**RULE**: All collectors MUST use the centralized collector configuration.

```python
# ✅ CORRECT - Use centralized collector config
from shared.table_config import get_collector_config

# Get configuration for onchain collector
config = get_collector_config("onchain_collector")
primary_table = config["primary_table"]        # "crypto_onchain_data"
reference_tables = config["reference_tables"]  # ["crypto_assets"]
```

### **🏭 Available Collector Configurations**

1. **Onchain Collector**
   - Primary: `crypto_onchain_data`
   - Reference: `crypto_assets`
   - Deprecated: `crypto_onchain_data_enhanced`

2. **Price Collector**
   - Primary: `technical_indicators`
   - Reference: `crypto_assets`

3. **News Collector**
   - Primary: `crypto_news`
   - Reference: `crypto_assets`

---

## 📦 **KUBERNETES DEPLOYMENT CONFIGURATION**

### **🎯 ConfigMaps Must Reference Central Config**

**RULE**: All K8s ConfigMaps MUST import and use centralized configuration.

```yaml
# ✅ CORRECT - K8s ConfigMap using centralized config
apiVersion: v1
kind: ConfigMap
metadata:
  name: onchain-collector-config
data:
  collector.py: |
    # Import centralized configuration
    from shared.table_config import CRYPTO_TABLES, get_master_onchain_table
    from shared.database_config import get_db_connection
    
    # Use centralized table names
    MASTER_TABLES = {
        "ONCHAIN_DATA": CRYPTO_TABLES["ONCHAIN_DATA"],
        "ASSETS": CRYPTO_TABLES["ASSETS"]
    }
    
    # Use centralized database connection
    connection = get_db_connection()
```

```yaml
# ❌ WRONG - Hard-coded configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: collector-config
data:
  ONCHAIN_TABLE: "crypto_onchain_data"          # DON'T HARD-CODE
  DB_HOST: "172.22.32.1"                       # DON'T HARD-CODE
```

---

## 🛠️ **API CONFIGURATION**

### **📍 API Configuration Standards**

**RULE**: All APIs must use environment-driven configuration with validation.

```python
# ✅ CORRECT - Environment-driven API config
import os
from typing import Optional

class APIConfig:
    def __init__(self):
        self.coingecko_key = self._get_required_env("COINGECKO_API_KEY")
        self.fred_key = self._get_required_env("FRED_API_KEY")
        self.guardian_key = self._get_required_env("GUARDIAN_API_KEY")
        
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value
```

```python
# ❌ WRONG - Hard-coded API keys
api_key = "CG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # NEVER DO THIS
```

### **🔐 Environment Variables for APIs**

```bash
# External API keys (set in K8s secrets)
COINGECKO_API_KEY=CG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FRED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GUARDIAN_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
REDDIT_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📝 **DEVELOPMENT GUIDELINES**

### **🔄 Before Writing Any Code**

1. **Check Centralized Config**: Does the configuration already exist?
2. **Validate Table Names**: Use `validate_table_usage()` 
3. **Use Environment Variables**: Never hard-code configurations
4. **Import Centralized Modules**: Use `shared/table_config.py` and `shared/database_config.py`

### **✅ Code Review Checklist**

- [ ] No hard-coded table names
- [ ] No hard-coded database credentials  
- [ ] No hard-coded API keys
- [ ] Uses centralized table configuration
- [ ] Uses centralized database configuration
- [ ] Validates table names before use
- [ ] Uses environment variables for configuration
- [ ] Includes error handling for missing config

### **🧪 Testing Requirements**

```python
# All tests must validate centralized config usage
def test_collector_uses_centralized_config():
    from shared.table_config import CRYPTO_TABLES
    
    # Test that collector uses centralized table names
    collector = OnchainCollector()
    assert collector.table_name == CRYPTO_TABLES["ONCHAIN_DATA"]
    
def test_database_connection_uses_centralized_config():
    from shared.database_config import get_db_connection
    
    # Test that database connection uses centralized config
    connection = get_db_connection()
    assert connection is not None
```

---

## 📚 **DOCUMENTATION UPDATES**

### **🎯 All Documentation Must Reference Central Config**

1. **Update README.md**: Reference centralized configuration
2. **Update Deployment Guides**: Show centralized config usage
3. **Update Integration Guides**: Demonstrate centralized patterns
4. **Update API Documentation**: Show environment variable usage

### **📖 Required Documentation Sections**

Each guide must include:

- **Centralized Configuration**: How to use `shared/table_config.py`
- **Environment Variables**: Required environment variables
- **Validation**: How to validate configurations
- **Examples**: Code examples using centralized config

---

## 🚨 **ENFORCEMENT**

### **⛔ Prohibited Actions**

1. **❌ Hard-coding table names** in any code
2. **❌ Hard-coding database credentials** in any code  
3. **❌ Hard-coding API keys** in any code
4. **❌ Creating new tables** without updating centralized config
5. **❌ Bypassing centralized configuration** for any reason

### **✅ Required Actions**

1. **✅ Use centralized table registry** for all table references
2. **✅ Use centralized database config** for all connections
3. **✅ Validate configurations** before use
4. **✅ Update centralized config** when adding new tables/APIs
5. **✅ Use environment variables** for all external configuration

---

## 🔧 **MIGRATION GUIDE FOR EXISTING CODE**

### **Step 1: Identify Hard-coded Values**

```bash
# Find hard-coded table names
grep -r "crypto_onchain_data" --include="*.py" .
grep -r "technical_indicators" --include="*.py" .

# Find hard-coded database config
grep -r "host.docker.internal" --include="*.py" .
grep -r "news_collector" --include="*.py" .
```

### **Step 2: Replace with Centralized Config**

```python
# Before
table_name = "crypto_onchain_data"

# After
from shared.table_config import CRYPTO_TABLES
table_name = CRYPTO_TABLES["ONCHAIN_DATA"]
```

### **Step 3: Test and Validate**

```python
# Add validation
from shared.table_config import validate_table_usage
result = validate_table_usage(table_name)
assert result["status"] == "approved"
```

---

## 📞 **SUPPORT**

For questions about centralized configuration:

1. **Check this document first**
2. **Review `shared/table_config.py`** for table configurations
3. **Review `shared/database_config.py`** for database configurations
4. **Test configurations** using provided validation functions

**Remember**: Centralized configuration prevents confusion, reduces errors, and ensures consistency across the entire system! 🚀