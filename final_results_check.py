#!/usr/bin/env python3
import mysql.connector

def check_final_results():
    """Check final improvements in data population"""
    conn = mysql.connector.connect(
        host='127.0.0.1', 
        user='news_collector', 
        password='99Rules!', 
        database='crypto_prices'
    )
    cursor = conn.cursor(dictionary=True)

    # Check current status
    cursor.execute('SELECT * FROM ml_features_materialized WHERE symbol = "BTC" ORDER BY timestamp_iso DESC LIMIT 1')
    btc_record = cursor.fetchone()

    if btc_record:
        populated = len([col for col, val in btc_record.items() if val is not None])
        rate = populated/86*100
        print(f'🎯 FINAL RESULT: BTC has {populated}/86 columns populated ({rate:.1f}%)')
        
        # Show recent improvement
        original_rate = 16.3
        improvement = rate - original_rate
        print(f'📈 Improvement: +{improvement:.1f} percentage points from {original_rate}%')
        
        # Check if technical indicators are now current
        cursor.execute('SELECT COUNT(*) as recent FROM technical_indicators WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 MINUTE)')
        recent_tech = cursor.fetchone()['recent']
        print(f'✅ Recent technical indicators: {recent_tech} records in last 30 min')
        
        # Check macro data population
        cursor.execute('SELECT vix, spx, dxy, treasury_10y FROM ml_features_materialized WHERE symbol = "BTC" ORDER BY timestamp_iso DESC LIMIT 1')
        macro_data = cursor.fetchone()
        macro_populated = len([col for col, val in macro_data.items() if val is not None])
        print(f'📊 Macro data: {macro_populated}/4 populated (VIX: {macro_data["vix"]}, SPX: {macro_data["spx"]})')

    conn.close()

if __name__ == "__main__":
    check_final_results()