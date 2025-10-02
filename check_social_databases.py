#!/usr/bin/env python3
"""
Check social media database configuration and fix connection issues
"""
import mysql.connector

def check_social_databases():
    try:
        print("🔍 CHECKING SOCIAL MEDIA DATABASE CONFIGURATION")
        print("=" * 60)
        
        # Check if crypto_sentiment_db exists
        try:
            conn = mysql.connector.connect(
                host='host.docker.internal',
                user='news_collector',
                password='99Rules!'
            )
            cursor = conn.cursor()
            
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            print(f"Available databases: {databases}")
            
            if 'crypto_sentiment_db' in databases:
                print("✅ crypto_sentiment_db exists")
            else:
                print("❌ crypto_sentiment_db does NOT exist")
            
            if 'crypto_news' in databases:
                print("✅ crypto_news exists")
                
                # Check social media tables in crypto_news
                cursor.execute("USE crypto_news")
                cursor.execute("SHOW TABLES")
                tables = [table[0] for table in cursor.fetchall()]
                print(f"Tables in crypto_news: {tables}")
                
                social_tables = [t for t in tables if 'social' in t.lower()]
                print(f"Social-related tables: {social_tables}")
                
                if 'social_media_posts' in tables:
                    cursor.execute("SELECT COUNT(*) FROM social_media_posts")
                    count = cursor.fetchone()[0]
                    print(f"Records in social_media_posts: {count:,}")
                    
                    if count > 0:
                        cursor.execute("SELECT MAX(created_at) FROM social_media_posts")
                        latest = cursor.fetchone()[0]
                        print(f"Latest social media post: {latest}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error checking databases: {e}")
        
        print("\n🔧 FIXING SOCIAL COLLECTOR DATABASE CONNECTION")
        print("The social-other service is configured to use 'crypto_sentiment_db'")
        print("but should use 'crypto_news' database like other collectors.")
        print("\nRecommendations:")
        print("1. Update social-other service environment variables")
        print("2. Restart the service with correct database configuration")
        print("3. Test collection after database fix")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in database check: {e}")
        return False

if __name__ == "__main__":
    check_social_databases()