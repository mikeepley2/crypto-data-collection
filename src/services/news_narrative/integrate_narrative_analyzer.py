#!/usr/bin/env python3
"""
News Narrative Integration Script
================================

Integrates the News Narrative Analyzer with your existing crypto data collection system:
- Connects to your aitest Ollama service
- Enhances your existing news impact scorer
- Processes your crypto_news database
- Generates narrative insights for your 320+ symbols

Usage:
    python integrate_narrative_analyzer.py --setup-db
    python integrate_narrative_analyzer.py --analyze-recent
    python integrate_narrative_analyzer.py --full-analysis
"""

import asyncio
import argparse
import logging
import mysql.connector
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NarrativeIntegration:
    """Integration manager for narrative analysis"""
    
    def __init__(self):
        # Your existing service endpoints
        self.ollama_endpoint = "http://localhost:8050"  # Your aitest Ollama service
        self.news_scorer_endpoint = "http://localhost:8036"  # Your news impact scorer
        self.narrative_analyzer_endpoint = "http://localhost:8039"  # New narrative service
        
        # Database config
        self.db_config = {
            'host': 'host.docker.internal',
            'user': 'news_collector', 
            'password': '99Rules!',
            'database': 'crypto_prices',
            'charset': 'utf8mb4'
        }
    
    def get_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def setup_database_schema(self):
        """Set up database schema for narrative analysis"""
        logger.info("🔧 Setting up narrative analysis database schema...")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Read and execute schema
            with open('src/services/news_narrative/schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute each statement separately
            statements = schema_sql.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Database schema setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database schema setup failed: {e}")
            return False
    
    def check_service_health(self):
        """Check health of all required services"""
        logger.info("🔍 Checking service health...")
        
        services = {
            "Ollama LLM (aitest)": self.ollama_endpoint,
            "News Impact Scorer": self.news_scorer_endpoint,
            "Narrative Analyzer": self.narrative_analyzer_endpoint
        }
        
        for service_name, endpoint in services.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: Healthy")
                else:
                    logger.warning(f"⚠️ {service_name}: Unhealthy (Status: {response.status_code})")
            except Exception as e:
                logger.error(f"❌ {service_name}: Not accessible - {e}")
    
    def analyze_recent_news(self, hours_back: int = 24):
        """Analyze recent news for narratives"""
        logger.info(f"📰 Analyzing news from the last {hours_back} hours...")
        
        try:
            # Get recent unanalyzed news
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT cn.id, cn.title, cn.published_date
            FROM crypto_news cn
            LEFT JOIN news_narratives nn ON cn.id = nn.news_id  
            WHERE cn.published_date >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            AND nn.news_id IS NULL
            ORDER BY cn.published_date DESC
            LIMIT 20
            """
            
            cursor.execute(query, (hours_back,))
            articles = cursor.fetchall()
            conn.close()
            
            logger.info(f"📊 Found {len(articles)} articles to analyze")
            
            # Analyze each article
            analyzed_count = 0
            for article in articles:
                try:
                    response = requests.post(
                        f"{self.narrative_analyzer_endpoint}/analyze-narrative/{article['id']}",
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('result'):
                            analyzed_count += 1
                            logger.info(f"✅ Analyzed: {article['title'][:50]}...")
                        else:
                            logger.warning(f"⚠️ No result for: {article['title'][:50]}...")
                    else:
                        logger.error(f"❌ Failed to analyze: {article['title'][:50]}...")
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing article {article['id']}: {e}")
                
                # Small delay to avoid overwhelming services
                asyncio.sleep(2)
            
            logger.info(f"🎉 Successfully analyzed {analyzed_count}/{len(articles)} articles")
            return analyzed_count
            
        except Exception as e:
            logger.error(f"❌ Error in recent news analysis: {e}")
            return 0
    
    def get_narrative_summary(self, days_back: int = 7):
        """Get narrative analysis summary"""
        logger.info(f"📈 Getting narrative summary for the last {days_back} days...")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Theme distribution
            query = """
            SELECT primary_theme, COUNT(*) as count, 
                   AVG(confidence_score) as avg_confidence,
                   AVG(narrative_sentiment) as avg_sentiment
            FROM news_narratives 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY primary_theme
            ORDER BY count DESC
            """
            
            cursor.execute(query, (days_back,))
            theme_stats = cursor.fetchall()
            
            # Top narratives
            query = """
            SELECT title, primary_theme, narrative_summary, confidence_score, narrative_sentiment
            FROM news_narratives 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            AND confidence_score > 0.7
            ORDER BY confidence_score DESC
            LIMIT 10
            """
            
            cursor.execute(query, (days_back,))
            top_narratives = cursor.fetchall()
            
            conn.close()
            
            # Print summary
            print(f"\n📊 NARRATIVE ANALYSIS SUMMARY ({days_back} days)")
            print("=" * 50)
            
            print("\n🎯 Theme Distribution:")
            for theme in theme_stats:
                print(f"   {theme['primary_theme'].title()}: {theme['count']} articles "
                      f"(Confidence: {theme['avg_confidence']:.2f}, "
                      f"Sentiment: {theme['avg_sentiment']:+.2f})")
            
            print(f"\n🏆 Top {len(top_narratives)} High-Confidence Narratives:")
            for i, narrative in enumerate(top_narratives, 1):
                print(f"   {i}. [{narrative['primary_theme'].upper()}] "
                      f"{narrative['title'][:60]}...")
                print(f"      Summary: {narrative['narrative_summary'][:100]}...")
                print(f"      Confidence: {narrative['confidence_score']:.2f}, "
                      f"Sentiment: {narrative['narrative_sentiment']:+.2f}\n")
            
            return len(theme_stats), len(top_narratives)
            
        except Exception as e:
            logger.error(f"❌ Error getting narrative summary: {e}")
            return 0, 0
    
    def run_full_analysis(self):
        """Run comprehensive narrative analysis"""
        logger.info("🚀 Starting full narrative analysis...")
        
        # Check services
        self.check_service_health()
        
        # Analyze recent news (last 3 days)
        analyzed = self.analyze_recent_news(hours_back=72)
        
        if analyzed > 0:
            # Get summary
            themes, narratives = self.get_narrative_summary(days_back=7)
            
            print(f"\n🎉 ANALYSIS COMPLETE!")
            print(f"   📰 Analyzed: {analyzed} articles")
            print(f"   🎯 Themes identified: {themes}")
            print(f"   🏆 High-confidence narratives: {narratives}")
            
            # Suggest next steps
            print(f"\n🔮 NEXT STEPS:")
            print("   1. Monitor trending themes in your trading strategies")
            print("   2. Set up alerts for high-impact narratives")
            print("   3. Integrate narrative sentiment with your ML models")
            print("   4. Use theme analysis for portfolio positioning")
        
        return analyzed > 0

def main():
    parser = argparse.ArgumentParser(description="News Narrative Integration")
    parser.add_argument('--setup-db', action='store_true', help='Set up database schema')
    parser.add_argument('--analyze-recent', action='store_true', help='Analyze recent news')
    parser.add_argument('--full-analysis', action='store_true', help='Run full analysis')
    parser.add_argument('--summary', action='store_true', help='Get narrative summary')
    parser.add_argument('--hours', type=int, default=24, help='Hours back for analysis')
    parser.add_argument('--days', type=int, default=7, help='Days back for summary')
    
    args = parser.parse_args()
    
    integration = NarrativeIntegration()
    
    if args.setup_db:
        integration.setup_database_schema()
    elif args.analyze_recent:
        integration.analyze_recent_news(args.hours)
    elif args.full_analysis:
        integration.run_full_analysis()
    elif args.summary:
        integration.get_narrative_summary(args.days)
    else:
        print("Please specify an action: --setup-db, --analyze-recent, --full-analysis, or --summary")

if __name__ == "__main__":
    main()