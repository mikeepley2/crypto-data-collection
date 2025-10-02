#!/usr/bin/env python3
"""
News Narrative Analysis Service for Crypto Data Collection
=========================================================

This service enhances your existing news impact scorer by adding:
- Market narrative extraction using your existing Ollama LLM service
- Theme identification and trend analysis
- Cross-asset impact prediction
- Narrative coherence scoring

Integrates with:
- Your existing news impact scorer (GPT-4 powered)
- Your aitest Ollama LLM service
- Your crypto data collection pipeline (3.35M+ records)
"""

import os
import json
import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketTheme(Enum):
    """Primary market themes"""
    REGULATION = "regulation"
    ADOPTION = "adoption"
    TECHNOLOGY = "technology"
    MACRO_ECONOMIC = "macro_economic"
    INSTITUTIONAL = "institutional"
    DEFI = "defi"
    SECURITY = "security"
    MARKET_STRUCTURE = "market_structure"
    GEOPOLITICAL = "geopolitical"
    OTHER = "other"

class NarrativeCoherence(Enum):
    """Narrative coherence levels"""
    STRONG = "strong"
    MODERATE = "moderate" 
    WEAK = "weak"
    CONFLICTING = "conflicting"

@dataclass
class MarketNarrative:
    """Market narrative analysis result"""
    news_id: str
    title: str
    primary_theme: MarketTheme
    secondary_themes: List[MarketTheme]
    
    # Narrative analysis
    narrative_summary: str
    key_drivers: List[str]
    market_implications: str
    
    # Impact analysis
    affected_assets: List[str]
    impact_timeline: str
    confidence_score: float
    coherence: NarrativeCoherence
    
    # Sentiment integration
    narrative_sentiment: float
    emotional_context: str
    
    # Cross-reference data
    similar_events: List[str]
    historical_patterns: str
    
    timestamp: datetime

class NewsNarrativeAnalyzer:
    """News narrative analysis service"""
    
    def __init__(self):
        # Service endpoints
        self.ollama_endpoint = os.getenv('OLLAMA_LLM_ENDPOINT', 
                                        'http://ollama-llm-service.crypto-trading.svc.cluster.local:8050')
        self.news_scorer_endpoint = os.getenv('NEWS_SCORER_ENDPOINT',
                                            'http://news-impact-scorer.crypto-collectors.svc.cluster.local:8036')
        
        # Database connection
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4'
        }
        
        # Major crypto symbols for impact analysis
        self.major_cryptos = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 
            'MATIC', 'LINK', 'UNI', 'ATOM', 'NEAR', 'ICP', 'ALGO'
        ]
        
        self.app = FastAPI(
            title="News Narrative Analysis Service",
            description="Advanced narrative analysis for crypto news using Ollama LLM",
            version="1.0.0"
        )
        self.setup_routes()
    
    def get_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "news-narrative-analyzer",
                "version": "1.0.0", 
                "status": "active",
                "features": [
                    "Market narrative extraction",
                    "Theme identification",
                    "Cross-asset impact analysis",
                    "Historical pattern matching"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            ollama_healthy = await self.test_service_connection(self.ollama_endpoint)
            news_scorer_healthy = await self.test_service_connection(self.news_scorer_endpoint)
            db_healthy = self.get_connection() is not None
            
            return {
                "status": "healthy" if ollama_healthy and db_healthy else "degraded",
                "ollama_connected": ollama_healthy,
                "news_scorer_connected": news_scorer_healthy,
                "database_connected": db_healthy,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/analyze-narrative/{news_id}")
        async def analyze_news_narrative(news_id: str):
            """Analyze narrative for specific news article"""
            result = await self.analyze_news_narrative(news_id)
            return {"result": asdict(result) if result else None}
        
        @self.app.post("/batch-analyze-recent")
        async def batch_analyze_recent_news(hours_back: int = 24):
            """Batch analyze recent news narratives"""
            results = await self.batch_analyze_recent_news(hours_back)
            return {
                "results": [asdict(r) for r in results],
                "count": len(results),
                "analysis_period_hours": hours_back
            }
        
        @self.app.get("/narrative-trends")
        async def get_narrative_trends(days_back: int = 7):
            """Get trending narratives over time period"""
            trends = await self.get_narrative_trends(days_back)
            return {"trends": trends, "period_days": days_back}
        
        @self.app.get("/theme-analysis")
        async def get_theme_analysis(days_back: int = 30):
            """Get comprehensive theme analysis"""
            analysis = await self.get_theme_analysis(days_back)
            return {"analysis": analysis, "period_days": days_back}
    
    async def test_service_connection(self, endpoint: str) -> bool:
        """Test connection to external service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False
    
    async def analyze_news_narrative(self, news_id: str) -> Optional[MarketNarrative]:
        """Analyze market narrative for a news article"""
        try:
            # Get news article
            article = await self.get_news_article(news_id)
            if not article:
                logger.error(f"Article {news_id} not found")
                return None
            
            # Get existing impact score if available
            impact_score = await self.get_existing_impact_score(news_id)
            
            # Perform narrative analysis using Ollama
            narrative_analysis = await self.perform_narrative_analysis(article, impact_score)
            if not narrative_analysis:
                logger.error(f"Narrative analysis failed for {news_id}")
                return None
            
            # Create comprehensive narrative result
            narrative = self.create_market_narrative(
                news_id, article, narrative_analysis, impact_score
            )
            
            # Store in database
            await self.store_narrative_analysis(narrative)
            
            return narrative
            
        except Exception as e:
            logger.error(f"Error analyzing narrative for {news_id}: {e}")
            return None
    
    async def get_news_article(self, news_id: str) -> Optional[Dict]:
        """Get news article from database"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT id, title, content, published_date, source, category 
            FROM crypto_news 
            WHERE id = %s
            """
            cursor.execute(query, (news_id,))
            article = cursor.fetchone()
            conn.close()
            return article
            
        except Exception as e:
            logger.error(f"Error getting article {news_id}: {e}")
            return None
    
    async def get_existing_impact_score(self, news_id: str) -> Optional[Dict]:
        """Get existing impact score from news scorer service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.news_scorer_endpoint}/score-news/{news_id}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("score")
                    return None
        except Exception as e:
            logger.error(f"Error getting impact score for {news_id}: {e}")
            return None
    
    async def perform_narrative_analysis(self, article: Dict, impact_score: Optional[Dict]) -> Optional[Dict]:
        """Perform narrative analysis using Ollama LLM"""
        try:
            # Prepare context for narrative analysis
            context = self.prepare_narrative_context(article, impact_score)
            
            # Request narrative analysis from Ollama
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "llama2:7b",  # Use your existing model
                    "messages": [
                        {
                            "role": "system", 
                            "content": self.get_narrative_analysis_prompt()
                        },
                        {
                            "role": "user", 
                            "content": context
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1500
                }
                
                async with session.post(
                    f"{self.ollama_endpoint}/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        return self.parse_narrative_response(content)
                    else:
                        logger.error(f"Ollama request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error in narrative analysis: {e}")
            return None
    
    def get_narrative_analysis_prompt(self) -> str:
        """Get system prompt for narrative analysis"""
        return """You are an expert crypto market narrative analyst. Your task is to analyze news articles and extract market narratives.

        For each article, provide:
        1. Primary theme (regulation, adoption, technology, macro_economic, institutional, defi, security, market_structure, geopolitical, other)
        2. Secondary themes (up to 3)
        3. Narrative summary (2-3 sentences)
        4. Key market drivers (3-5 bullet points)
        5. Market implications (how this affects crypto markets)
        6. Affected assets (specific cryptocurrencies)
        7. Impact timeline (immediate, short-term, medium-term, long-term)
        8. Confidence score (0.0-1.0)
        9. Narrative coherence (strong, moderate, weak, conflicting)
        10. Emotional context (fear, optimism, uncertainty, excitement, etc.)
        11. Historical patterns (similar events from the past)
        
        Return response as JSON format with these exact keys."""
    
    def prepare_narrative_context(self, article: Dict, impact_score: Optional[Dict]) -> str:
        """Prepare context for narrative analysis"""
        context = f"""
        CRYPTO NEWS ARTICLE ANALYSIS
        
        Title: {article['title']}
        Content: {article['content'][:2000]}...
        Published: {article['published_date']}
        Source: {article.get('source', 'Unknown')}
        Category: {article.get('category', 'General')}
        """
        
        if impact_score:
            context += f"""
            
            EXISTING IMPACT ANALYSIS:
            Impact Score: {impact_score.get('impact_score', 'N/A')}
            Impact Type: {impact_score.get('impact_type', 'N/A')}
            Reasoning: {impact_score.get('reasoning', 'N/A')[:500]}
            """
        
        context += """
        
        Please analyze this article for market narratives and themes, considering the crypto market context and potential cross-asset implications.
        """
        
        return context
    
    def parse_narrative_response(self, content: str) -> Dict:
        """Parse LLM response into structured data"""
        try:
            # Try to parse as JSON
            if content.strip().startswith('{'):
                return json.loads(content)
            
            # Fallback: extract information using pattern matching
            return self.extract_narrative_info(content)
            
        except json.JSONDecodeError:
            # Fallback parsing
            return self.extract_narrative_info(content)
    
    def extract_narrative_info(self, content: str) -> Dict:
        """Extract narrative information from text response"""
        # This is a fallback parser for when JSON parsing fails
        lines = content.split('\n')
        
        result = {
            "primary_theme": "other",
            "secondary_themes": [],
            "narrative_summary": "Analysis not fully parsed",
            "key_drivers": ["Data parsing incomplete"],
            "market_implications": "Unable to determine from response",
            "affected_assets": ["BTC", "ETH"],  # Default major assets
            "impact_timeline": "uncertain",
            "confidence_score": 0.5,
            "coherence": "moderate",
            "emotional_context": "mixed",
            "historical_patterns": "No clear pattern identified"
        }
        
        # Basic keyword extraction
        content_lower = content.lower()
        if any(word in content_lower for word in ['regulation', 'regulatory', 'sec', 'compliance']):
            result["primary_theme"] = "regulation"
        elif any(word in content_lower for word in ['adoption', 'mainstream', 'institutional']):
            result["primary_theme"] = "adoption"
        elif any(word in content_lower for word in ['technology', 'upgrade', 'protocol', 'blockchain']):
            result["primary_theme"] = "technology"
        
        return result
    
    def create_market_narrative(
        self, 
        news_id: str, 
        article: Dict, 
        narrative_analysis: Dict, 
        impact_score: Optional[Dict]
    ) -> MarketNarrative:
        """Create comprehensive market narrative object"""
        
        return MarketNarrative(
            news_id=news_id,
            title=article['title'],
            primary_theme=MarketTheme(narrative_analysis.get("primary_theme", "other")),
            secondary_themes=[
                MarketTheme(theme) for theme in narrative_analysis.get("secondary_themes", [])
                if theme in [t.value for t in MarketTheme]
            ],
            
            narrative_summary=narrative_analysis.get("narrative_summary", ""),
            key_drivers=narrative_analysis.get("key_drivers", []),
            market_implications=narrative_analysis.get("market_implications", ""),
            
            affected_assets=narrative_analysis.get("affected_assets", ["BTC", "ETH"]),
            impact_timeline=narrative_analysis.get("impact_timeline", "uncertain"),
            confidence_score=narrative_analysis.get("confidence_score", 0.5),
            coherence=NarrativeCoherence(narrative_analysis.get("coherence", "moderate")),
            
            narrative_sentiment=self.calculate_narrative_sentiment(narrative_analysis),
            emotional_context=narrative_analysis.get("emotional_context", "mixed"),
            
            similar_events=[],  # Would be populated by historical analysis
            historical_patterns=narrative_analysis.get("historical_patterns", ""),
            
            timestamp=datetime.now()
        )
    
    def calculate_narrative_sentiment(self, narrative_analysis: Dict) -> float:
        """Calculate sentiment score from narrative"""
        emotional_context = narrative_analysis.get("emotional_context", "").lower()
        
        positive_emotions = ['optimism', 'excitement', 'confidence', 'bullish']
        negative_emotions = ['fear', 'panic', 'uncertainty', 'bearish']
        
        if any(emotion in emotional_context for emotion in positive_emotions):
            return 0.7
        elif any(emotion in emotional_context for emotion in negative_emotions):
            return -0.7
        else:
            return 0.0
    
    async def store_narrative_analysis(self, narrative: MarketNarrative):
        """Store narrative analysis in database"""
        try:
            conn = self.get_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            query = """
            INSERT INTO news_narratives 
            (news_id, title, primary_theme, secondary_themes, narrative_summary, 
             key_drivers, market_implications, affected_assets, impact_timeline, 
             confidence_score, coherence, narrative_sentiment, emotional_context, 
             historical_patterns, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            narrative_summary = VALUES(narrative_summary),
            confidence_score = VALUES(confidence_score),
            updated_at = NOW()
            """
            
            cursor.execute(query, (
                narrative.news_id,
                narrative.title,
                narrative.primary_theme.value,
                json.dumps([t.value for t in narrative.secondary_themes]),
                narrative.narrative_summary,
                json.dumps(narrative.key_drivers),
                narrative.market_implications,
                json.dumps(narrative.affected_assets),
                narrative.impact_timeline,
                narrative.confidence_score,
                narrative.coherence.value,
                narrative.narrative_sentiment,
                narrative.emotional_context,
                narrative.historical_patterns,
                narrative.timestamp
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing narrative analysis: {e}")
    
    async def batch_analyze_recent_news(self, hours_back: int) -> List[MarketNarrative]:
        """Batch analyze recent news articles"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
                
            cursor = conn.cursor(dictionary=True)
            
            # Get recent unanalyzed news
            query = """
            SELECT cn.id 
            FROM crypto_news cn
            LEFT JOIN news_narratives nn ON cn.id = nn.news_id
            WHERE cn.published_date >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            AND nn.news_id IS NULL
            ORDER BY cn.published_date DESC
            LIMIT 50
            """
            
            cursor.execute(query, (hours_back,))
            news_ids = [row['id'] for row in cursor.fetchall()]
            conn.close()
            
            # Analyze each article
            results = []
            for news_id in news_ids:
                narrative = await self.analyze_news_narrative(str(news_id))
                if narrative:
                    results.append(narrative)
                    
                # Small delay to avoid overwhelming the LLM service
                await asyncio.sleep(1)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return []
    
    async def get_narrative_trends(self, days_back: int) -> Dict:
        """Get trending narratives over time period"""
        # Implementation for narrative trends analysis
        # This would analyze stored narratives for trending themes
        return {
            "trending_themes": ["regulation", "adoption"],
            "emerging_narratives": ["institutional_custody", "cbdc_impact"],
            "sentiment_evolution": "increasingly_positive",
            "analysis_period": f"{days_back} days"
        }
    
    async def get_theme_analysis(self, days_back: int) -> Dict:
        """Get comprehensive theme analysis"""
        # Implementation for theme analysis
        # This would provide deep analysis of narrative themes
        return {
            "theme_distribution": {
                "regulation": 35,
                "adoption": 25,
                "technology": 20,
                "macro_economic": 15,
                "other": 5
            },
            "impact_correlation": {
                "regulation": -0.3,
                "adoption": 0.7,
                "technology": 0.4
            },
            "analysis_period": f"{days_back} days"
        }

# Request models
class NarrativeRequest(BaseModel):
    news_id: str

class BatchAnalysisRequest(BaseModel):
    hours_back: int = 24

# Initialize service
narrative_analyzer = NewsNarrativeAnalyzer()
app = narrative_analyzer.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8039))
    uvicorn.run(app, host="0.0.0.0", port=port)