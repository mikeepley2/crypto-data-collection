#!/usr/bin/env python3

import sys
sys.path.append('/app')
from realtime_materialized_updater import RealTimeMaterializedTableUpdater

print('📊 Checking macro economic data integration...')

updater = RealTimeMaterializedTableUpdater()
connection = updater.get_db_connection()

with connection.cursor() as cursor:
    # Check recent macro data in materialized table
    cursor.execute("""
        SELECT 
            COUNT(*) as total_recent,
            COUNT(vix) as vix_count,
            COUNT(spx) as spx_count, 
            COUNT(dxy) as dxy_count,
            COUNT(btc_fear_greed) as fear_greed_count,
            MAX(vix) as latest_vix,
            MAX(spx) as latest_spx,
            MAX(dxy) as latest_dxy
        FROM ml_features_materialized 
        WHERE DATE(timestamp_iso) >= '2025-09-26'
    """)
    
    result = cursor.fetchone()
    if result:
        total, vix_c, spx_c, dxy_c, fg_c, l_vix, l_spx, l_dxy = result
        
        print(f'📈 Recent Records (Sept 26): {total:,}')
        print(f'📊 VIX populated: {vix_c:,} / {total:,} ({(vix_c/total*100) if total > 0 else 0:.1f}%)')
        print(f'📊 SPX populated: {spx_c:,} / {total:,} ({(spx_c/total*100) if total > 0 else 0:.1f}%)')
        print(f'📊 DXY populated: {dxy_c:,} / {total:,} ({(dxy_c/total*100) if total > 0 else 0:.1f}%)')
        print(f'😱 Fear & Greed: {fg_c:,} / {total:,} ({(fg_c/total*100) if total > 0 else 0:.1f}%)')
        print()
        print(f'🔍 Latest Values:')
        print(f'   VIX: {l_vix if l_vix else "N/A"}')
        print(f'   SPX: {l_spx if l_spx else "N/A"}') 
        print(f'   DXY: {l_dxy if l_dxy else "N/A"}')

    # Check what macro data is available in source table
    print()
    print('🔍 Checking source macro_indicators table...')
    cursor.execute("""
        SELECT indicator_name, value, data_date 
        FROM macro_indicators 
        WHERE DATE(data_date) >= '2025-09-26'
        ORDER BY data_date DESC, indicator_name
        LIMIT 10
    """)
    
    macro_data = cursor.fetchall()
    if macro_data:
        print('📊 Recent macro indicators:')
        for indicator, value, date in macro_data:
            print(f'   {indicator}: {value} ({date})')
    else:
        print('⚠️ No recent macro data found in source table')

connection.close()
print()
print('✅ Macro data integration check complete!')