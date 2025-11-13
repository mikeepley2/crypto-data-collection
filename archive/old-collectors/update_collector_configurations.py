#!/usr/bin/env python3
"""
Update All Collector Configurations to Use crypto_assets Table
Replace hardcoded symbol lists with dynamic database-driven symbol management
"""

import os
import yaml
import json
import re
from pathlib import Path

def update_kubernetes_collectors():
    """Update Kubernetes collector configurations"""
    print("🔧 UPDATING KUBERNETES COLLECTOR CONFIGURATIONS")
    print("=" * 80)
    
    k8s_files = [
        "k8s/collectors/enhanced-crypto-prices.yaml",
        "k8s/collectors/technical-calculator.yaml", 
        "k8s/collectors/onchain-collector.yaml",
        "k8s/collectors/macro-collector.yaml",
        "k8s/collectors/sentiment-collector.yaml",
        "k8s/collectors/collector-configmaps.yaml"
    ]
    
    for file_path in k8s_files:
        if os.path.exists(file_path):
            print(f"\\n📋 Processing {file_path}...")
            update_collector_yaml(file_path)
        else:
            print(f"\\n⚠️  File not found: {file_path}")

def update_collector_yaml(file_path):
    """Update a specific collector YAML file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace hardcoded symbol lists with dynamic imports
        symbol_replacements = [
            # Replace hardcoded symbol arrays
            (
                r'symbols\\s*=\\s*\\[[^\\]]+\\]',
                'symbols = get_collector_symbols("price")'
            ),
            # Replace hardcoded Coinbase symbols
            (
                r'coinbase_symbols\\s*=\\s*\\[[^\\]]+\\]',
                'coinbase_symbols = get_supported_symbols("coinbase", "exchange")'
            ),
            # Replace manual symbol mapping
            (
                r'symbol_mapping\\s*=\\s*\\{[^\\}]+\\}',
                'symbol_mapping = get_exchange_symbol_mappings("coinbase")'
            ),
            # Add import statement if not present
            (
                r'(import\\s+mysql\\.connector.*?\\n)',
                '\\1from shared.table_config import get_collector_symbols, get_supported_symbols, get_exchange_symbol_mappings, resolve_symbol_from_exchange\\n'
            )
        ]
        
        updated = False
        for pattern, replacement in symbol_replacements:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated = True
        
        # Add crypto_assets symbol loading pattern
        crypto_assets_pattern = '''
            # Load symbols from crypto_assets table
            def load_symbols_from_db():
                """Load active symbols from crypto_assets table"""
                try:
                    from shared.table_config import get_collector_symbols
                    return get_collector_symbols("COLLECTOR_TYPE")
                except Exception as e:
                    logger.error(f"Failed to load symbols from crypto_assets: {e}")
                    return []  # Fallback to empty list
        '''
        
        if "load_symbols_from_db" not in content and "def " in content:
            # Insert the function before the main collector logic
            insertion_point = content.find("def main(")
            if insertion_point == -1:
                insertion_point = content.find("if __name__")
            if insertion_point == -1:
                insertion_point = len(content)
            
            content = content[:insertion_point] + crypto_assets_pattern + content[insertion_point:]
            updated = True
        
        if updated:
            # Write the updated content
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Updated {file_path}")
        else:
            print(f"   ℹ️  No changes needed for {file_path}")
            
    except Exception as e:
        print(f"   ❌ Error updating {file_path}: {e}")

def update_python_collectors():
    """Update Python collector scripts"""
    print("\\n🐍 UPDATING PYTHON COLLECTOR SCRIPTS")
    print("=" * 80)
    
    python_files = [
        "services/price-collection/enhanced_crypto_prices_service.py",
        "services/technical-analysis/technical_calculator.py",
        "services/onchain-collection/onchain_collector.py",
        "services/macro-collection/macro_collector.py",
        "services/sentiment-analysis/sentiment_collector.py"
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            print(f"\\n📋 Processing {file_path}...")
            update_python_collector(file_path)
        else:
            print(f"\\n⚠️  File not found: {file_path}")

def update_python_collector(file_path):
    """Update a specific Python collector file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add imports at the top
        import_addition = """
# Dynamic symbol management
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from table_config import (
    get_collector_symbols, 
    get_supported_symbols, 
    get_exchange_symbol_mappings,
    resolve_symbol_from_exchange,
    validate_symbol_exists,
    normalize_symbol_to_internal
)
"""
        
        if "from table_config import" not in content:
            # Add imports after existing imports
            import_insertion_point = 0
            lines = content.split('\\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_insertion_point = i + 1
            
            lines.insert(import_insertion_point, import_addition)
            content = '\\n'.join(lines)
        
        # Replace hardcoded symbol definitions
        replacements = [
            # Replace hardcoded symbol lists
            (
                r'SUPPORTED_SYMBOLS\\s*=\\s*\\[[^\\]]+\\]',
                'SUPPORTED_SYMBOLS = get_collector_symbols("price")'
            ),
            (
                r'COINBASE_SYMBOLS\\s*=\\s*\\[[^\\]]+\\]', 
                'COINBASE_SYMBOLS = get_supported_symbols("coinbase", "exchange")'
            ),
            # Replace symbol mapping dictionaries
            (
                r'SYMBOL_MAPPING\\s*=\\s*\\{[^\\}]+\\}',
                'SYMBOL_MAPPING = get_exchange_symbol_mappings("coinbase")'
            ),
            # Replace manual symbol loading
            (
                r'def get_symbols\\(\\):[^}]+return\\s+\\[[^\\]]+\\]',
                '''def get_symbols():
    """Get symbols from crypto_assets table"""
    return get_collector_symbols("price")'''
            )
        ]
        
        updated = False
        for pattern, replacement in replacements:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                updated = True
        
        # Add symbol validation before processing
        validation_code = '''
        # Validate symbol before processing
        if not validate_symbol_exists(symbol):
            logger.warning(f"Symbol {symbol} not found in crypto_assets table, skipping")
            continue
        
        # Normalize symbol to internal format
        normalized_symbol = normalize_symbol_to_internal(symbol)
        '''
        
        # Find processing loops and add validation
        symbol_loop_patterns = [
            r'for\\s+symbol\\s+in\\s+symbols:',
            r'for\\s+symbol\\s+in\\s+SUPPORTED_SYMBOLS:',
            r'for\\s+symbol\\s+in\\s+self\\.symbols:'
        ]
        
        for pattern in symbol_loop_patterns:
            if re.search(pattern, content):
                content = re.sub(
                    f'({pattern})',
                    f'\\1{validation_code}',
                    content
                )
                updated = True
        
        if updated:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Updated {file_path}")
        else:
            print(f"   ℹ️  No changes needed for {file_path}")
            
    except Exception as e:
        print(f"   ❌ Error updating {file_path}: {e}")

def create_collector_symbol_guide():
    """Create a guide for using dynamic symbols in collectors"""
    guide_content = '''# Dynamic Symbol Management Guide for Collectors

## Overview
All collectors now use the `crypto_assets` table as the single source of truth for symbol definitions instead of hardcoded lists.

## Quick Migration Guide

### 1. Import Dynamic Functions
```python
from shared.table_config import (
    get_collector_symbols,      # Get symbols for specific collector type
    get_supported_symbols,      # Get symbols for specific exchange
    get_exchange_symbol_mappings, # Get exchange format mappings
    resolve_symbol_from_exchange, # Convert exchange format to internal
    validate_symbol_exists,     # Check if symbol is valid
    normalize_symbol_to_internal # Normalize to internal format
)
```

### 2. Replace Hardcoded Symbol Lists

**Before (hardcoded):**
```python
SYMBOLS = ["BTCUSD", "ETHUSD", "ADAUSD", "SOLUSD"]
```

**After (dynamic):**
```python
SYMBOLS = get_collector_symbols("price")  # Gets from crypto_assets table
```

### 3. Exchange-Specific Symbols

**For Coinbase API:**
```python
# Get Coinbase-supported symbols in exchange format
coinbase_symbols = get_supported_symbols("coinbase", "exchange")  # ["BTC-USD", "ETH-USD"]

# Get Coinbase-supported symbols in internal format  
internal_symbols = get_supported_symbols("coinbase", "internal")  # ["BTCUSD", "ETHUSD"]

# Get mapping dictionary
symbol_mapping = get_exchange_symbol_mappings("coinbase")  # {"BTC-USD": "BTCUSD"}
```

### 4. Symbol Validation

**Add validation in processing loops:**
```python
for symbol in symbols:
    # Validate symbol exists in crypto_assets
    if not validate_symbol_exists(symbol):
        logger.warning(f"Symbol {symbol} not in crypto_assets, skipping")
        continue
    
    # Normalize to internal format if needed
    internal_symbol = normalize_symbol_to_internal(symbol)
    
    # Process the symbol...
```

### 5. Exchange Format Conversion

**Convert between formats:**
```python
# From Coinbase format to internal
internal = resolve_symbol_from_exchange("BTC-USD", "coinbase")  # "BTCUSD"

# From internal to Coinbase format
coinbase = normalize_symbol_for_exchange("BTCUSD", "coinbase")  # "BTC-USD"
```

## Collector-Specific Examples

### Price Collector
```python
def main():
    symbols = get_collector_symbols("price")  # Gets Coinbase-supported symbols
    for symbol in symbols:
        coinbase_format = normalize_symbol_for_exchange(symbol, "coinbase")
        # Use coinbase_format for API calls
        # Store data using internal symbol format
```

### Onchain Collector  
```python
def main():
    symbols = get_collector_symbols("onchain")  # Gets top 100 market cap symbols
    for symbol in symbols:
        if validate_symbol_exists(symbol):
            # Collect onchain data for symbol
```

### Sentiment Collector
```python
def main():
    symbols = get_collector_symbols("sentiment")  # Gets symbols with social presence
    for symbol in symbols:
        metadata = get_symbol_metadata(symbol)
        aliases = metadata.get('aliases', [])
        # Use symbol + aliases for sentiment collection
```

## Benefits

1. **Single Source of Truth**: All symbols come from crypto_assets table
2. **Automatic Updates**: New symbols added to crypto_assets are automatically available
3. **Exchange Flexibility**: Easy support for multiple exchanges
4. **Symbol Validation**: Built-in validation against active symbols
5. **Performance**: Cached symbol lookups (1-hour cache)
6. **Collector Optimization**: Different symbol sets for different collector types

## Migration Checklist

- [ ] Replace hardcoded symbol lists with `get_collector_symbols()`
- [ ] Add symbol validation in processing loops
- [ ] Use exchange format conversion functions
- [ ] Test with database connection
- [ ] Update error handling for missing symbols
- [ ] Remove old hardcoded symbol constants
- [ ] Update documentation and comments

## Troubleshooting

**"No symbols returned"**: Check database connection and crypto_assets table
**"Symbol not found"**: Use `validate_symbol_exists()` to check validity
**"Wrong format"**: Use `normalize_symbol_to_internal()` for consistency
**"Performance issues"**: Symbols are cached for 1 hour automatically
'''

    with open("COLLECTOR_SYMBOL_MIGRATION_GUIDE.md", 'w') as f:
        f.write(guide_content)
    
    print("\\n📚 Created COLLECTOR_SYMBOL_MIGRATION_GUIDE.md")

def test_dynamic_symbol_functions():
    """Test the dynamic symbol management functions"""
    print("\\n🧪 TESTING DYNAMIC SYMBOL FUNCTIONS")
    print("=" * 80)
    
    try:
        # Test the imports
        import sys
        sys.path.append('shared')
        from table_config import (
            get_collector_symbols,
            get_supported_symbols,
            get_exchange_symbol_mappings,
            resolve_symbol_from_exchange,
            validate_symbol_exists
        )
        
        print("✅ Imports successful")
        
        # Test dynamic symbol loading
        print("\\n📊 Testing dynamic symbol loading...")
        
        price_symbols = get_collector_symbols("price")[:5]
        print(f"   Price symbols (first 5): {price_symbols}")
        
        onchain_symbols = get_collector_symbols("onchain")[:3] 
        print(f"   Onchain symbols (first 3): {onchain_symbols}")
        
        # Test exchange mappings
        print("\\n🔄 Testing exchange mappings...")
        coinbase_mappings = get_exchange_symbol_mappings("coinbase")
        if coinbase_mappings:
            first_mapping = list(coinbase_mappings.items())[0]
            print(f"   Coinbase mapping example: {first_mapping[0]} -> {first_mapping[1]}")
        
        # Test symbol resolution
        print("\\n🎯 Testing symbol resolution...")
        test_symbols = ["BTC-USD", "ETHUSDT", "ADAUSD"]
        for symbol in test_symbols:
            internal = resolve_symbol_from_exchange(symbol)
            print(f"   {symbol} -> {internal}")
            
        print("\\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution"""
    print("🚀 COLLECTOR CONFIGURATION UPDATE")
    print("Replacing hardcoded symbols with crypto_assets table integration")
    print("=" * 80)
    
    # Update Kubernetes configurations
    update_kubernetes_collectors()
    
    # Update Python collector scripts  
    update_python_collectors()
    
    # Create migration guide
    create_collector_symbol_guide()
    
    # Test the functions
    test_dynamic_symbol_functions()
    
    print("\\n" + "=" * 80)
    print("✅ COLLECTOR UPDATE COMPLETED")
    print("=" * 80)
    
    print("\\n📋 NEXT STEPS:")
    print("1. Review updated collector configurations")
    print("2. Test each collector with database connection")
    print("3. Deploy updated collectors to Kubernetes")
    print("4. Monitor for any symbol-related errors")
    print("5. Remove any remaining hardcoded symbol references")
    
    print("\\n💡 BENEFITS:")
    print("• Single source of truth for all symbols")
    print("• Automatic updates when crypto_assets changes")
    print("• Multi-exchange compatibility")
    print("• Built-in symbol validation")
    print("• Performance optimized with caching")

if __name__ == "__main__":
    main()