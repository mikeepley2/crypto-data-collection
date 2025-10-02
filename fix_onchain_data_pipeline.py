#!/usr/bin/env python3

import mysql.connector
from datetime import datetime, timedelta

def main():
    print("=== ONCHAIN DATA PIPELINE REPAIR ===")
    print("Fixing crypto_onchain_data_enhanced population issue")
    
    connection = mysql.connector.connect(
        host='localhost',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )
    print("✅ Database connected")
    
    cursor = connection.cursor()
    
    # 1. Check current state
    print(f"\n1. CURRENT ONCHAIN DATA STATE:")
    cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data")
    base_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data_enhanced")  
    enhanced_count = cursor.fetchone()[0]
    
    print(f"   crypto_onchain_data: {base_count:,} records")
    print(f"   crypto_onchain_data_enhanced: {enhanced_count:,} records")
    print(f"   Missing: {base_count - enhanced_count:,} records ({((base_count - enhanced_count)/base_count)*100:.1f}%)")
    
    if enhanced_count >= base_count * 0.9:
        print("✅ Onchain data pipeline is healthy, no action needed")
        return
    
    # 2. Check table structures
    print(f"\n2. ANALYZING TABLE STRUCTURES:")
    cursor.execute("DESCRIBE crypto_onchain_data")
    base_cols = [col[0] for col in cursor.fetchall()]
    
    cursor.execute("DESCRIBE crypto_onchain_data_enhanced")
    enhanced_cols = [col[0] for col in cursor.fetchall()]
    
    print(f"   Base table columns: {len(base_cols)}")
    print(f"   Enhanced table columns: {len(enhanced_cols)}")
    
    # Find common columns for copying
    common_cols = list(set(base_cols) & set(enhanced_cols))
    print(f"   Common columns: {len(common_cols)}")
    
    # 3. Check data freshness
    cursor.execute("SELECT MAX(timestamp), MIN(timestamp) FROM crypto_onchain_data")
    base_latest, base_earliest = cursor.fetchone()
    
    cursor.execute("SELECT MAX(timestamp), MIN(timestamp) FROM crypto_onchain_data_enhanced WHERE timestamp IS NOT NULL")
    enhanced_result = cursor.fetchone()
    enhanced_latest = enhanced_result[0] if enhanced_result[0] else None
    enhanced_earliest = enhanced_result[1] if enhanced_result[1] else None
    
    print(f"\n3. DATA FRESHNESS:")
    print(f"   Base table: {base_earliest} to {base_latest}")
    if enhanced_latest:
        print(f"   Enhanced table: {enhanced_earliest} to {enhanced_latest}")
        gap_hours = (base_latest - enhanced_latest).total_seconds() / 3600
        print(f"   Freshness gap: {gap_hours:.1f} hours")
    else:
        print(f"   Enhanced table: No data")
    
    # 4. Repair strategy
    print(f"\n4. REPAIR STRATEGY:")
    if enhanced_count < 1000:  # Very low count, likely complete rebuild needed
        print("   Strategy: Complete rebuild of enhanced table")
        repair_method = "rebuild"
    else:
        print("   Strategy: Incremental sync of missing records")  
        repair_method = "sync"
    
    # 5. Execute repair
    print(f"\n5. EXECUTING REPAIR ({repair_method.upper()}):")
    
    if repair_method == "rebuild":
        # Clear and rebuild enhanced table
        print("   Step 1: Backing up enhanced table...")
        cursor.execute("CREATE TABLE crypto_onchain_data_enhanced_backup_repair AS SELECT * FROM crypto_onchain_data_enhanced")
        
        print("   Step 2: Clearing enhanced table...")
        cursor.execute("DELETE FROM crypto_onchain_data_enhanced")
        
        print("   Step 3: Copying base data to enhanced table...")
        # Copy common columns from base to enhanced
        common_cols_str = ', '.join([f"`{col}`" for col in common_cols])
        
        insert_query = f"""
            INSERT INTO crypto_onchain_data_enhanced ({common_cols_str})
            SELECT {common_cols_str}
            FROM crypto_onchain_data
        """
        
        cursor.execute(insert_query)
        copied_records = cursor.rowcount
        
        print(f"   ✅ Copied {copied_records:,} records to enhanced table")
        
    else:  # sync method
        # Find missing records and copy them
        print("   Step 1: Finding missing records...")
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM crypto_onchain_data b
            LEFT JOIN crypto_onchain_data_enhanced e 
            ON b.id = e.id OR (b.coin_symbol = e.coin_symbol AND b.timestamp = e.timestamp)
            WHERE e.id IS NULL
        """)
        
        missing_count = cursor.fetchone()[0]
        print(f"   Missing records: {missing_count:,}")
        
        if missing_count > 0:
            print("   Step 2: Copying missing records...")
            
            common_cols_str = ', '.join([f"`{col}`" for col in common_cols])
            
            sync_query = f"""
                INSERT INTO crypto_onchain_data_enhanced ({common_cols_str})
                SELECT {common_cols_str}
                FROM crypto_onchain_data b
                LEFT JOIN crypto_onchain_data_enhanced e 
                ON b.id = e.id OR (b.coin_symbol = e.coin_symbol AND b.timestamp = e.timestamp)
                WHERE e.id IS NULL
            """
            
            cursor.execute(sync_query)
            copied_records = cursor.rowcount
            print(f"   ✅ Copied {copied_records:,} missing records")
        else:
            print("   ✅ No missing records to copy")
    
    # 6. Commit and verify
    connection.commit()
    
    cursor.execute("SELECT COUNT(*) FROM crypto_onchain_data_enhanced")
    final_count = cursor.fetchone()[0]
    
    print(f"\n6. REPAIR RESULTS:")
    print(f"   Before: {enhanced_count:,} records")
    print(f"   After: {final_count:,} records") 
    print(f"   Added: {final_count - enhanced_count:,} records")
    
    success_rate = (final_count / base_count) * 100
    print(f"   Success rate: {success_rate:.1f}%")
    
    if success_rate > 95:
        print("   ✅ REPAIR SUCCESSFUL - Onchain pipeline restored")
    elif success_rate > 80:
        print("   ⚠️ REPAIR PARTIAL - Significant improvement but gaps remain")
    else:
        print("   ❌ REPAIR FAILED - Manual investigation needed")
    
    cursor.close()
    connection.close()
    
    print(f"\n🏁 ONCHAIN DATA PIPELINE REPAIR COMPLETE")

if __name__ == "__main__":
    main()