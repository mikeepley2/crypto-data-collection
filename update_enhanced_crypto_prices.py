#!/usr/bin/env python3
"""
Update Enhanced Crypto Prices Service to use the enhanced tables
Switch from price_data (71K records) to price_data_real (3.8M records) or hourly_data (3.3M records)
"""

import subprocess
import time

def update_enhanced_crypto_prices_config():
    """Update the enhanced-crypto-prices service to use the enhanced tables"""
    
    print("UPDATING ENHANCED CRYPTO PRICES CONFIGURATION")
    print("=" * 60)
    
    # Create a patch to update environment variables
    patch_config = '''
spec:
  template:
    spec:
      containers:
      - name: enhanced-crypto-prices
        env:
        - name: CRYPTO_PRICES_TABLE
          value: "hourly_data"
        - name: HIGH_COLUMN
          value: "high"
        - name: LOW_COLUMN
          value: "low"
        - name: OPEN_COLUMN
          value: "open"
        - name: CLOSE_COLUMN
          value: "close"
        - name: VOLUME_COLUMN
          value: "volume"
'''
    
    # Write patch to file
    with open('enhanced-prices-patch.yaml', 'w') as f:
        f.write(patch_config)
    
    print("1. ANALYSIS:")
    print("-" * 15)
    print("   Current: price_data (71,905 records, 21 columns)")
    print("   Enhanced Options:")
    print("   - price_data_real (3,796,993 records, 49 columns) - COMPREHENSIVE")
    print("   - hourly_data (3,357,222 records, 7 columns, ACTIVE) - OHLCV")
    
    print("\n2. RECOMMENDATION:")
    print("-" * 20)
    print("   Use hourly_data for:")
    print("   - Active real-time collection (710 recent records)")
    print("   - Standard OHLCV format (Open, High, Low, Close, Volume)")
    print("   - Compatible with existing collector logic")
    
    print("\n3. APPLYING CONFIGURATION UPDATE:")
    print("-" * 40)
    
    try:
        # Apply the patch to update environment variables
        cmd = "kubectl patch deployment enhanced-crypto-prices -n crypto-collectors --patch-file enhanced-prices-patch.yaml"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Successfully updated enhanced-crypto-prices deployment")
            print("   📝 Changed CRYPTO_PRICES_TABLE from 'price_data' to 'hourly_data'")
            
            # Wait for rollout
            print("\n4. WAITING FOR ROLLOUT:")
            print("-" * 25)
            time.sleep(5)
            
            # Check rollout status
            cmd = "kubectl rollout status deployment/enhanced-crypto-prices -n crypto-collectors --timeout=60s"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Deployment rollout completed successfully")
            else:
                print(f"   ⚠️  Rollout status: {result.stdout}")
                
        else:
            print(f"   ❌ Failed to update deployment: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Error updating configuration: {e}")
    
    print("\n5. VERIFICATION:")
    print("-" * 15)
    print("   The enhanced-crypto-prices service should now:")
    print("   - Write to hourly_data (3.3M records) instead of price_data (71K records)")
    print("   - Use proper OHLCV column names (open, high, low, close, volume)")
    print("   - Benefit from the much larger, actively updated dataset")
    
    print("\n6. NEXT STEPS:")
    print("-" * 15)
    print("   1. Monitor data collection to hourly_data")
    print("   2. Verify new records are being inserted")
    print("   3. Consider also updating to use price_data_real for comprehensive features")
    
    # Create alternative patch for price_data_real
    print("\n7. ALTERNATIVE: USE COMPREHENSIVE price_data_real TABLE")
    print("-" * 55)
    
    comprehensive_patch = '''
spec:
  template:
    spec:
      containers:
      - name: enhanced-crypto-prices
        env:
        - name: CRYPTO_PRICES_TABLE
          value: "price_data_real"
        - name: HIGH_COLUMN
          value: "high_24h"
        - name: LOW_COLUMN
          value: "low_24h"
        - name: OPEN_COLUMN
          value: "open_24h"
        - name: CLOSE_COLUMN
          value: "current_price"
        - name: VOLUME_COLUMN
          value: "volume_usd_24h"
'''
    
    with open('enhanced-prices-comprehensive-patch.yaml', 'w') as f:
        f.write(comprehensive_patch)
    
    print("   Created enhanced-prices-comprehensive-patch.yaml")
    print("   This would use price_data_real (3.8M records, 49 columns)")
    print("   Includes technical indicators, market cap, supply data, etc.")
    
    return True

if __name__ == "__main__":
    update_enhanced_crypto_prices_config()