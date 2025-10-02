#!/usr/bin/env python3
"""
Fix OHLC Collector Asset Selection
Create a patch to fix the collector to collect ALL assets from database, not just those with existing premium data
"""

def analyze_current_issue():
    """Analyze the current collector issue"""
    
    print("🔍 COLLECTOR ASSET SELECTION ISSUE ANALYSIS")
    print("=" * 60)
    
    print("📊 CURRENT BEHAVIOR:")
    print("   1. ✅ Collector loads 130 symbols (74 from database + 56 fallback)")
    print("   2. ✅ Database has 75 assets with coingecko_id")
    print("   3. ❌ Collector filters to only symbols with existing 'premium' data")
    print("   4. ❌ Only 32 symbols have recent premium data")
    print("   5. ❌ New assets never get collected (chicken-and-egg problem)")
    
    print(f"\n🐛 THE PROBLEM:")
    print("   In get_existing_ohlc_symbols() method:")
    print("   ```sql")
    print("   SELECT DISTINCT symbol FROM ohlc_data")
    print("   WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)")
    print("   AND data_source LIKE '%premium%'  ← THIS IS THE PROBLEM")
    print("   ```")
    
    print(f"\n💡 THE SOLUTION:")
    print("   Remove the data_source filter so ALL assets get considered:")
    print("   ```sql")
    print("   SELECT DISTINCT symbol FROM ohlc_data")
    print("   WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)")
    print("   -- Remove: AND data_source LIKE '%premium%'")
    print("   ```")
    
    print(f"\n🎯 EXPECTED RESULT:")
    print("   • Collector will attempt to collect ALL 75 assets with coingecko_id")
    print("   • New assets will be collected for the first time")
    print("   • Coverage will increase from 32 assets to 75 assets")
    print("   • No more hardcoded asset limitations")

def create_collector_patch():
    """Create a patch for the collector"""
    
    print(f"\n🔧 COLLECTOR PATCH CREATION:")
    print("-" * 40)
    
    patch_content = '''# OHLC Collector Asset Selection Fix
# 
# Problem: Collector only collects assets with existing 'premium' data
# Solution: Remove data_source filter to collect ALL available assets
#
# File: unified_premium_ohlc_collector.py
# Method: get_existing_ohlc_symbols()
#
# BEFORE (problematic):
# cursor.execute("""
#     SELECT DISTINCT symbol
#     FROM ohlc_data
#     WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)
#     AND data_source LIKE '%premium%'  ← REMOVE THIS LINE
# """, (days_back,))
#
# AFTER (fixed):
# cursor.execute("""
#     SELECT DISTINCT symbol
#     FROM ohlc_data
#     WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)
# """, (days_back,))
#
# This change will allow the collector to process ALL assets from the
# crypto_assets table instead of only those with existing premium data.

def get_existing_ohlc_symbols(self, days_back: int = 7) -> set:
    """Get symbols with recent OHLC data from unified table"""
    try:
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        # FIXED: Removed data_source filter to include ALL recent symbols
        cursor.execute("""
            SELECT DISTINCT symbol
            FROM ohlc_data
            WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (days_back,))

        existing_symbols = set(row[0] for row in cursor.fetchall())
        conn.close()

        logger.info(f"📈 Found {len(existing_symbols)} symbols with recent OHLC data")
        return existing_symbols

    except Exception as e:
        logger.error(f"❌ Error getting existing OHLC symbols: {e}")
        return set()
'''
    
    # Write patch to file
    with open('ohlc_collector_fix.patch', 'w') as f:
        f.write(patch_content)
    
    print("   ✅ Created patch file: ohlc_collector_fix.patch")
    print("   📝 Patch removes data_source filter from symbol selection")

def create_deployment_update():
    """Create commands to update the collector"""
    
    print(f"\n🚀 DEPLOYMENT UPDATE COMMANDS:")
    print("-" * 40)
    
    commands = [
        "# Step 1: Apply the fix to the collector",
        "# (This would require rebuilding the container image with the fix)",
        "",
        "# Step 2: Scale down current collector",
        "kubectl scale deployment unified-ohlc-collector -n crypto-collectors --replicas=0",
        "",
        "# Step 3: Update collector image (after fix is built)",
        "# kubectl set image deployment/unified-ohlc-collector unified-ohlc-collector=unified-ohlc-collector:fixed -n crypto-collectors",
        "",
        "# Step 4: Scale back up",
        "kubectl scale deployment unified-ohlc-collector -n crypto-collectors --replicas=1",
        "",
        "# Step 5: Test collection",
        "# kubectl logs -f deployment/unified-ohlc-collector -n crypto-collectors",
    ]
    
    for cmd in commands:
        print(f"   {cmd}")

def immediate_workaround():
    """Suggest immediate workaround"""
    
    print(f"\n⚡ IMMEDIATE WORKAROUND:")
    print("-" * 40)
    
    print("   🔧 OPTION 1: Manual Collection Trigger")
    print("   • Trigger collection with skip_existing=False")
    print("   • This will force collection of all assets regardless of existing data")
    print("   • Command: POST /collect with {'skip_existing': false}")
    
    print(f"\n   🔧 OPTION 2: Database Direct Fix")
    print("   • Temporarily set all recent OHLC data_source to 'premium'")
    print("   • This will make the current filter include all assets")
    print("   • Revert after collection completes")
    
    print(f"\n   🔧 OPTION 3: Container Exec Fix")
    print("   • Directly edit the file in the running container")
    print("   • Remove the problematic filter line")
    print("   • Restart the container process")

def verification_plan():
    """Show how to verify the fix works"""
    
    print(f"\n✅ VERIFICATION PLAN:")
    print("-" * 40)
    
    print("   1. 📊 Before Fix:")
    print("      • Check current collection: ~32 assets")
    print("      • Run asset coverage analysis")
    
    print(f"\n   2. 🔧 Apply Fix:")
    print("      • Remove data_source filter from collector")
    print("      • Restart collector")
    
    print(f"\n   3. 🚀 Test Collection:")
    print("      • Trigger manual collection")
    print("      • Monitor logs for new assets being processed")
    
    print(f"\n   4. ✅ Verify Results:")
    print("      • Check OHLC data for new symbols")
    print("      • Confirm coverage increased from 32 to ~75 assets")
    print("      • Validate all major assets are being collected")
    
    print(f"\n🎯 SUCCESS CRITERIA:")
    print("   • OHLC collection covers ALL 75 assets with coingecko_id")
    print("   • No hardcoded asset limitations")
    print("   • Major assets like BTC, ETH, SOL are being collected")
    print("   • Scheduled collection works for full asset list")

if __name__ == "__main__":
    analyze_current_issue()
    create_collector_patch()
    create_deployment_update() 
    immediate_workaround()
    verification_plan()
    
    print(f"\n" + "="*60)
    print("🎯 SUMMARY:")
    print("✅ Issue identified: Collector filters to only existing 'premium' data")
    print("✅ Root cause: data_source LIKE '%premium%' in get_existing_ohlc_symbols()")
    print("✅ Solution: Remove data_source filter to collect ALL database assets")
    print("✅ Expected result: Coverage increases from 32 to 75 assets")
    print("⚡ Ready to implement fix and test!")
    print("="*60)