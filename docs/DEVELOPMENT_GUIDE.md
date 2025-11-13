# 🚀 Development Guide - Centralized Configuration Standards

## 🎯 **MANDATORY FOR ALL DEVELOPERS**

**⚠️ CRITICAL**: This guide MUST be followed for all development work. No exceptions.

---

## 📋 **PRE-DEVELOPMENT CHECKLIST**

Before writing any code, ensure you:

- [ ] Read [`CENTRALIZED_CONFIG_INSTRUCTIONS.md`](../CENTRALIZED_CONFIG_INSTRUCTIONS.md) completely
- [ ] Understand the centralized table registry in [`shared/table_config.py`](../shared/table_config.py)
- [ ] Understand the centralized database config in [`shared/database_config.py`](../shared/database_config.py)
- [ ] Have the required environment variables configured
- [ ] Know which tables your code will interact with

---

## 🔧 **DEVELOPMENT STANDARDS**

### **1. Table Name Usage - MANDATORY**

```python
# ✅ CORRECT - Always use centralized table registry
from shared.table_config import CRYPTO_TABLES, TECHNICAL_TABLES, ML_TABLES

# Access master tables
onchain_table = CRYPTO_TABLES["ONCHAIN_DATA"]      # "crypto_onchain_data"
assets_table = CRYPTO_TABLES["ASSETS"]             # "crypto_assets"
ml_features_table = ML_TABLES["FEATURES"]          # "ml_features_materialized"
```

```python
# ❌ WRONG - Never hard-code table names
table_name = "crypto_onchain_data"                  # DON'T DO THIS
table_name = "ml_features_materialized"             # DON'T DO THIS
```

### **2. Database Connections - MANDATORY**

```python
# ✅ CORRECT - Always use centralized database configuration
from shared.database_config import get_db_connection, test_db_connection

# Test connection first
if not test_db_connection():
    raise ConnectionError("Database connection failed")

# Get connection using centralized config
connection = get_db_connection()
```

```python
# ❌ WRONG - Never hard-code database configuration
import mysql.connector
config = {
    'host': '172.22.32.1',
    'user': 'news_collector',
    'password': '99Rules!',
    'database': 'crypto_prices'
}
connection = mysql.connector.connect(**config)      # DON'T DO THIS
```

### **3. Table Validation - MANDATORY**

```python
# ✅ CORRECT - Always validate table names before use
from shared.table_config import validate_table_usage

def use_table(table_name: str):
    # Validate table is approved
    validation = validate_table_usage(table_name)
    if validation["status"] != "approved":
        raise ValueError(f"Table not approved: {validation}")
    
    # Use the validated table
    return table_name
```

### **4. Environment Variables - MANDATORY**

```python
# ✅ CORRECT - Always use environment variables for configuration
import os
from typing import Optional

class ServiceConfig:
    def __init__(self):
        self.api_key = self._get_required_env("COINGECKO_API_KEY")
        self.db_host = os.getenv("DB_HOST", "172.22.32.1")
        self.db_user = os.getenv("DB_USER", "news_collector")
        
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value
```

```python
# ❌ WRONG - Never hard-code API keys or sensitive configuration
api_key = "CG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"    # DON'T DO THIS
db_password = "99Rules!"                            # DON'T DO THIS
```

---

## 🧱 **DEVELOPMENT PATTERNS**

### **Pattern 1: Data Collector Development**

```python
#!/usr/bin/env python3
"""
Example Data Collector - Following Centralized Configuration Standards
"""
import logging
from shared.table_config import CRYPTO_TABLES, get_collector_config
from shared.database_config import get_db_connection, test_db_connection

class ExampleCollector:
    def __init__(self):
        # Use centralized collector configuration
        self.config = get_collector_config("onchain_collector")
        self.primary_table = self.config["primary_table"]
        self.reference_tables = self.config["reference_tables"]
        
        # Test database connectivity
        if not test_db_connection():
            raise ConnectionError("Database connection failed")
            
        self.logger = logging.getLogger(__name__)
        
    def collect_data(self):
        """Collect data using centralized configuration"""
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            
            # Use centralized table names
            cursor.execute(f"""
                INSERT INTO {self.primary_table} 
                (asset_id, timestamp, data_value) 
                VALUES (%s, %s, %s)
            """, ("BTC", "2025-11-04", 67000))
            
            connection.commit()
            self.logger.info(f"Data inserted into {self.primary_table}")
            
        finally:
            connection.close()
```

### **Pattern 2: API Service Development**

```python
#!/usr/bin/env python3
"""
Example API Service - Following Centralized Configuration Standards
"""
from fastapi import FastAPI, HTTPException
from shared.table_config import CRYPTO_TABLES, ML_TABLES
from shared.database_config import get_db_connection

app = FastAPI(title="Example API Service")

@app.get("/api/v1/onchain/{symbol}")
async def get_onchain_data(symbol: str):
    """Get onchain data using centralized configuration"""
    
    # Use centralized table registry
    onchain_table = CRYPTO_TABLES["ONCHAIN_DATA"]
    
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"""
            SELECT * FROM {onchain_table} 
            WHERE asset_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
            
        return result
        
    finally:
        connection.close()
```

### **Pattern 3: Kubernetes Deployment Development**

```yaml
# ✅ CORRECT - K8s deployment using centralized configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-collector-config
data:
  collector.py: |
    # Import centralized configuration
    from shared.table_config import CRYPTO_TABLES, get_collector_config
    from shared.database_config import get_db_connection
    
    # Use centralized configuration
    config = get_collector_config("onchain_collector")
    MASTER_TABLES = {
        "ONCHAIN_DATA": CRYPTO_TABLES["ONCHAIN_DATA"],
        "ASSETS": CRYPTO_TABLES["ASSETS"]
    }
    
    # Use centralized database connection
    connection = get_db_connection()
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-collector
spec:
  template:
    spec:
      containers:
      - name: collector
        env:
        - name: DB_HOST
          value: "172.22.32.1"
        - name: DB_USER
          value: "news_collector"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: password
```

---

## 🧪 **TESTING STANDARDS**

### **Test Pattern 1: Configuration Testing**

```python
import pytest
from shared.table_config import CRYPTO_TABLES, validate_table_usage
from shared.database_config import test_db_connection

def test_centralized_table_config():
    """Test that centralized table configuration is working"""
    # Test table registry access
    assert CRYPTO_TABLES["ONCHAIN_DATA"] == "crypto_onchain_data"
    assert CRYPTO_TABLES["ASSETS"] == "crypto_assets"
    
    # Test table validation
    result = validate_table_usage("crypto_onchain_data")
    assert result["status"] == "approved"
    
    # Test deprecated table detection
    result = validate_table_usage("crypto_onchain_data_enhanced")
    assert result["status"] == "deprecated"

def test_centralized_database_config():
    """Test that centralized database configuration is working"""
    # Test database connectivity
    assert test_db_connection() is True
```

### **Test Pattern 2: Service Testing**

```python
import pytest
from unittest.mock import patch, MagicMock
from your_service import YourCollector

@patch('shared.database_config.get_db_connection')
@patch('shared.table_config.get_collector_config')
def test_collector_uses_centralized_config(mock_get_config, mock_get_connection):
    """Test that collector uses centralized configuration"""
    
    # Mock centralized configuration
    mock_get_config.return_value = {
        "primary_table": "crypto_onchain_data",
        "reference_tables": ["crypto_assets"]
    }
    mock_connection = MagicMock()
    mock_get_connection.return_value = mock_connection
    
    # Test collector initialization
    collector = YourCollector()
    assert collector.primary_table == "crypto_onchain_data"
    
    # Verify centralized config was used
    mock_get_config.assert_called_once_with("onchain_collector")
    mock_get_connection.assert_called()
```

---

## 📝 **CODE REVIEW CHECKLIST**

Before submitting any code, verify:

### **Configuration Compliance**
- [ ] No hard-coded table names
- [ ] No hard-coded database credentials
- [ ] No hard-coded API keys or endpoints
- [ ] All table references use `shared/table_config.py`
- [ ] All database connections use `shared/database_config.py`
- [ ] Environment variables used for all external configuration

### **Validation and Error Handling**
- [ ] Table names validated before use
- [ ] Database connection tested before use
- [ ] Proper error handling for missing configuration
- [ ] Graceful handling of configuration failures

### **Documentation and Testing**
- [ ] Code follows centralized configuration patterns
- [ ] Tests validate centralized configuration usage
- [ ] Configuration usage documented in code comments
- [ ] Environment variables documented

---

## 🚨 **COMMON MISTAKES TO AVOID**

### **❌ Hard-coded Table Names**
```python
# DON'T DO THIS
query = "SELECT * FROM crypto_onchain_data WHERE..."
table = "ml_features_materialized"
```

### **❌ Hard-coded Database Configuration**
```python
# DON'T DO THIS
config = {
    'host': 'host.docker.internal',
    'password': '99Rules!'
}
```

### **❌ Hard-coded API Keys**
```python
# DON'T DO THIS
api_key = "CG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
headers = {"x-cg-demo-api-key": "your-key-here"}
```

### **❌ Bypassing Validation**
```python
# DON'T DO THIS
# Just assume table exists without validation
cursor.execute("INSERT INTO some_table...")
```

---

## 🎯 **DEVELOPMENT WORKFLOW**

### **Step 1: Planning**
1. Review [`CENTRALIZED_CONFIG_INSTRUCTIONS.md`](../CENTRALIZED_CONFIG_INSTRUCTIONS.md)
2. Identify which tables your code will use
3. Validate table names using centralized registry
4. Plan environment variable usage

### **Step 2: Implementation**
1. Import centralized configuration modules
2. Use centralized table registry for all table references
3. Use centralized database configuration for connections
4. Implement proper validation and error handling

### **Step 3: Testing**
1. Write tests that validate centralized configuration usage
2. Test with missing environment variables
3. Test table validation functionality
4. Test database connection failure scenarios

### **Step 4: Code Review**
1. Use the code review checklist above
2. Verify no hard-coded values exist
3. Confirm centralized configuration is used consistently
4. Validate error handling is appropriate

---

## 📞 **SUPPORT**

If you have questions about centralized configuration:

1. **First**: Review [`CENTRALIZED_CONFIG_INSTRUCTIONS.md`](../CENTRALIZED_CONFIG_INSTRUCTIONS.md)
2. **Second**: Check the implementation in [`shared/table_config.py`](../shared/table_config.py)
3. **Third**: Look at examples in this development guide

**Remember**: Centralized configuration prevents confusion, reduces errors, and ensures consistency! 🚀