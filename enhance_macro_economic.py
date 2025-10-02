#!/usr/bin/env python3
"""
Macro Economic Data Backfill Enhancement Script
Enhances the existing macro economic data collection and performs historical backfill
"""

import mysql.connector
import requests
import os
from datetime import datetime, timedelta
import time

def get_db_connection():
    """Get database connection with proper credentials"""
    return mysql.connector.connect(
        host='host.docker.internal',
        user='news_collector',
        password='99Rules!',
        database='crypto_prices'
    )

def analyze_current_macro_data():
    """Analyze current macro economic data status"""
    print('📊 Analyzing current macro economic data...')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check recent macro data
        cursor.execute("""
            SELECT COUNT(*) FROM macro_indicators 
            WHERE DATE(timestamp) >= '2025-09-01'
        """)
        recent_count = cursor.fetchone()[0]
        
        # Check available indicators
        cursor.execute("""
            SELECT DISTINCT indicator_name FROM macro_indicators 
            ORDER BY indicator_name
        """)
        indicators = [row[0] for row in cursor.fetchall()]
        
        # Check recent activity by indicator
        cursor.execute("""
            SELECT indicator_name, COUNT(*) as count 
            FROM macro_indicators 
            WHERE DATE(timestamp) >= '2025-09-01' 
            GROUP BY indicator_name 
            ORDER BY count DESC
        """)
        indicator_counts = cursor.fetchall()
        
        print(f'📈 Total recent records: {recent_count}')
        print(f'📋 Available indicators: {len(indicators)} types')
        print('🎯 Recent activity breakdown:')
        for indicator, count in indicator_counts:
            print(f'  {indicator}: {count} records')
            
        cursor.close()
        connection.close()
        return recent_count, indicators, indicator_counts
        
    except Exception as e:
        print(f'❌ Error analyzing macro data: {e}')
        return 0, [], []

def fetch_fear_greed_index():
    """Fetch Fear & Greed Index data"""
    try:
        print('🎭 Fetching Fear & Greed Index...')
        # Alternative Fear & Greed Index API
        url = "https://api.alternative.me/fng/?limit=30"  # Last 30 days
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            print(f'✅ Retrieved {len(data["data"])} Fear & Greed records')
            return data['data']
        else:
            print('⚠️  No Fear & Greed data available')
            return []
            
    except Exception as e:
        print(f'❌ Error fetching Fear & Greed Index: {e}')
        return []

def store_fear_greed_data(fear_greed_data):
    """Store Fear & Greed Index data in database"""
    if not fear_greed_data:
        return 0
        
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        stored_count = 0
        for record in fear_greed_data:
            try:
                # Convert timestamp to datetime
                timestamp = datetime.fromtimestamp(int(record['timestamp']))
                value = float(record['value'])
                classification = record.get('value_classification', 'Unknown')
                
                # Insert or update
                cursor.execute("""
                    INSERT INTO macro_indicators 
                    (indicator_name, value, timestamp, metadata) 
                    VALUES ('FEAR_GREED_INDEX', %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    value = VALUES(value), 
                    metadata = VALUES(metadata)
                """, (value, timestamp, classification))
                
                stored_count += 1
                
            except Exception as e:
                print(f'⚠️  Error storing Fear & Greed record: {e}')
                continue
                
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f'✅ Stored {stored_count} Fear & Greed records')
        return stored_count
        
    except Exception as e:
        print(f'❌ Error storing Fear & Greed data: {e}')
        return 0

def enhance_macro_collection():
    """Enhance macro economic data collection"""
    print('🚀 Starting macro economic data enhancement...')
    
    # Analyze current state
    recent_count, indicators, indicator_counts = analyze_current_macro_data()
    
    # Fetch and store Fear & Greed Index if missing
    if 'FEAR_GREED_INDEX' not in indicators:
        print('🎭 Adding Fear & Greed Index data...')
        fear_greed_data = fetch_fear_greed_index()
        stored = store_fear_greed_data(fear_greed_data)
        
        if stored > 0:
            print(f'✅ Enhanced macro data with {stored} Fear & Greed records')
        else:
            print('⚠️  Could not add Fear & Greed Index data')
    else:
        print('✅ Fear & Greed Index already available')
    
    # Trigger existing macro collection to get latest data
    try:
        print('📈 Triggering macro economic data collection...')
        # Call the macro economic service
        response = requests.post(
            'http://localhost:8000/collect/realtime',
            timeout=30
        )
        if response.status_code == 200:
            print('✅ Macro economic collection triggered successfully')
        else:
            print(f'⚠️  Macro collection returned status {response.status_code}')
    except Exception as e:
        print(f'⚠️  Could not trigger macro collection: {e}')
    
    print('🎯 Macro economic enhancement completed!')

if __name__ == "__main__":
    enhance_macro_collection()