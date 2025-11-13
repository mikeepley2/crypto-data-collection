#!/usr/bin/env python3
"""
LLM-Powered News Impact Scoring Service
Analyzes news articles and predicts their potential market impact using LLM.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import mysql.connector
from mysql.connector import Error
import openai
import uvicorn
import numpy as np
from collections import defaultdict
import traceback
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NewsImpactScore:
    """News impact assessment."""
    news_id: str
    timestamp: datetime
    title: str
    content_preview: str
    impact_score: float  # 0-1 scale
    time_horizon: str  # immediate, short-term, medium-term, long-term
    affected_symbols: List[str]
    impact_type: str  # positive, negative, neutral
    confidence: float
    urgency_level: str  # low, medium, high, critical
    market_sectors: List[str]
    key_themes: List[str]
    price_prediction: Dict[str, float]  # symbol -> predicted % change
    llm_reasoning: str
    actionable_insights: List[str]

@dataclass
class MarketImpactSummary:
    """Summary of market impact from multiple news sources."""
    timestamp: datetime
    total_articles: int
    high_impact_articles: int
    bullish_sentiment: float
    bearish_sentiment: float
    top_themes: List[str]
    most_affected_symbols: List[str]
    overall_market_direction: str
    confidence: float
    llm_market_outlook: str

class NewsImpactScorer:
    """LLM-powered news impact scoring service."""
    
    def __init__(self):
        self.db_config = {
            'host': 'host.docker.internal',
            'user': 'news_collector',
            'password': '99Rules!',
            'database': 'crypto_prices'
        }
        
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI()
        
        # Impact thresholds
        self.high_impact_threshold = 0.7
        self.medium_impact_threshold = 0.4
        
        # Common crypto symbols for impact assessment
        self.major_cryptos = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']
        
        self.app = FastAPI(title="News Impact Scorer", version="1.0.0")
        self.setup_routes()
    
    def get_connection(self):
        """Get database connection."""
        try:
            return mysql.connector.connect(**self.db_config)
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            return {"status": "News Impact Scorer Active", "timestamp": datetime.now()}
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now()}
        
        @self.app.post("/score-news/{news_id}")
        async def score_news_article(news_id: str):
            """Score impact of a specific news article."""
            try:
                score = await self.score_news_impact(news_id)
                return {"score": score.__dict__ if score else None, "timestamp": datetime.now()}
            except Exception as e:
                logger.error(f"Error scoring news {news_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/recent-scores")
        async def get_recent_scores():
            """Get recent news impact scores."""
            try:
                scores = await self.get_recent_impact_scores()
                return {"scores": [score.__dict__ if hasattr(score, '__dict__') else score for score in scores], 
                       "timestamp": datetime.now()}
            except Exception as e:
                logger.error(f"Error getting recent scores: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/market-impact-summary")
        async def get_market_impact_summary():
            """Get market impact summary from recent news."""
            try:
                summary = await self.generate_market_impact_summary()
                return {"summary": summary.__dict__ if summary else None, "timestamp": datetime.now()}
            except Exception as e:
                logger.error(f"Error generating market impact summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/batch-score")
        async def batch_score_news():
            """Score all unprocessed news articles."""
            try:
                results = await self.batch_score_recent_news()
                return {"results": results, "timestamp": datetime.now()}
            except Exception as e:
                logger.error(f"Error in batch scoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/high-impact-alerts")
        async def get_high_impact_alerts():
            """Get high-impact news alerts."""
            try:
                alerts = await self.get_high_impact_news()
                return {"alerts": alerts, "timestamp": datetime.now()}
            except Exception as e:
                logger.error(f"Error getting high impact alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def score_news_impact(self, news_id: str) -> Optional[NewsImpactScore]:
        """Score the market impact of a news article."""
        try:
            # Get news article
            news_article = await self.get_news_article(news_id)
            if not news_article:
                return None
            
            # Get market context
            market_context = await self.get_market_context()
            
            # Get LLM impact analysis
            impact_analysis = await self.get_llm_impact_analysis(news_article, market_context)
            
            # Create impact score
            score = NewsImpactScore(
                news_id=news_id,
                timestamp=datetime.now(),
                title=news_article['title'],
                content_preview=news_article['content'][:200] + "..." if len(news_article['content']) > 200 else news_article['content'],
                impact_score=impact_analysis.get('impact_score', 0.5),
                time_horizon=impact_analysis.get('time_horizon', 'short-term'),
                affected_symbols=impact_analysis.get('affected_symbols', []),
                impact_type=impact_analysis.get('impact_type', 'neutral'),
                confidence=impact_analysis.get('confidence', 0.7),
                urgency_level=impact_analysis.get('urgency_level', 'medium'),
                market_sectors=impact_analysis.get('market_sectors', []),
                key_themes=impact_analysis.get('key_themes', []),
                price_prediction=impact_analysis.get('price_prediction', {}),
                llm_reasoning=impact_analysis.get('reasoning', ''),
                actionable_insights=impact_analysis.get('actionable_insights', [])
            )
            
            # Store the score
            await self.store_impact_score(score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring news impact for {news_id}: {e}")
            return None
    
    async def get_news_article(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get news article by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT 
                    id,
                    title,
                    content,
                    published_date,
                    source,
                    url,
                    sentiment_score
                FROM crypto_news 
                WHERE id = %s
                """
                
                cursor.execute(query, (news_id,))
                article = cursor.fetchone()
                
                return article
                
        except Exception as e:
            logger.error(f"Error getting news article {news_id}: {e}")
            return None
    
    async def get_market_context(self) -> Dict[str, Any]:
        """Get current market context for impact assessment."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Get recent price movements
                price_query = """
                SELECT 
                    symbol,
                    close_price,
                    price_change_24h,
                    price_change_7d,
                    volume,
                    market_cap
                FROM crypto_prices 
                WHERE symbol IN ('BTC', 'ETH', 'BNB', 'ADA', 'SOL')
                AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY market_cap DESC
                """
                
                cursor.execute(price_query)
                prices = cursor.fetchall()
                
                # Get recent sentiment
                sentiment_query = """
                SELECT 
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as sentiment_count
                FROM crypto_sentiment_data 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 HOUR)
                """
                
                cursor.execute(sentiment_query)
                sentiment_data = cursor.fetchone()
                
                # Calculate market volatility
                volatility_data = {}
                for price in prices:
                    symbol = price['symbol']
                    change_24h = abs(price['price_change_24h']) if price['price_change_24h'] else 0
                    volatility_data[symbol] = change_24h
                
                return {
                    'prices': prices,
                    'avg_sentiment': sentiment_data['avg_sentiment'] if sentiment_data else 0,
                    'sentiment_count': sentiment_data['sentiment_count'] if sentiment_data else 0,
                    'volatility': volatility_data,
                    'market_trend': self.assess_market_trend(prices)
                }
                
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return {}
    
    def assess_market_trend(self, prices: List[Dict]) -> str:
        """Assess overall market trend."""
        if not prices:
            return 'unknown'
        
        positive_count = sum(1 for p in prices if p['price_change_24h'] and p['price_change_24h'] > 0)
        total_count = len([p for p in prices if p['price_change_24h'] is not None])
        
        if total_count == 0:
            return 'unknown'
        
        positive_ratio = positive_count / total_count
        
        if positive_ratio >= 0.7:
            return 'bullish'
        elif positive_ratio <= 0.3:
            return 'bearish'
        else:
            return 'mixed'
    
    async def get_llm_impact_analysis(self, news_article: Dict, market_context: Dict) -> Dict[str, Any]:
        """Get LLM analysis of news impact."""
        try:
            # Prepare context for LLM
            market_summary = ""
            if market_context.get('prices'):
                for price in market_context['prices'][:5]:  # Top 5 cryptos
                    change_24h = price['price_change_24h'] or 0
                    market_summary += f"{price['symbol']}: {change_24h:+.2%} (24h), "
                market_summary = market_summary.rstrip(', ')
            
            context = f"""
            Analyze the market impact of this cryptocurrency news article:
            
            ARTICLE:
            Title: {news_article['title']}
            Content: {news_article['content'][:1000]}...
            Published: {news_article['published_date']}
            Source: {news_article.get('source', 'Unknown')}
            
            CURRENT MARKET CONTEXT:
            Market Trend: {market_context.get('market_trend', 'unknown')}
            Recent Price Changes: {market_summary}
            Overall Sentiment: {market_context.get('avg_sentiment', 0):.2f}
            
            Assess the potential market impact and provide:
            1. Impact score (0-1, where 1 is maximum market-moving potential)
            2. Time horizon (immediate/short-term/medium-term/long-term)
            3. Affected symbols (list of crypto symbols)
            4. Impact type (positive/negative/neutral)
            5. Confidence in assessment (0-1)
            6. Urgency level (low/medium/high/critical)
            7. Market sectors affected (DeFi, NFT, Layer1, etc.)
            8. Key themes (regulation, adoption, technology, etc.)
            9. Price prediction (symbol: % change expected)
            10. Actionable insights for traders
            11. Detailed reasoning
            
            Consider:
            - How significant is this news for the crypto market?
            - Which specific cryptocurrencies would be most affected?
            - What is the likely timeline for market reaction?
            - How does this fit with current market sentiment?
            
            Return as JSON format.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert crypto news analyst specializing in market impact assessment. Provide precise, actionable analysis in JSON format."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            try:
                # Parse JSON response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    result = self.parse_impact_fallback(content, news_article)
            except json.JSONDecodeError:
                result = self.parse_impact_fallback(content, news_article)
            
            # Validate and clean result
            result = self.validate_impact_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting LLM impact analysis: {e}")
            return self.get_default_impact_analysis(news_article)
    
    def parse_impact_fallback(self, content: str, news_article: Dict) -> Dict[str, Any]:
        """Fallback parsing for impact analysis."""
        # Basic keyword analysis
        title_lower = news_article['title'].lower()
        content_lower = news_article['content'].lower()
        
        # Impact keywords
        high_impact_keywords = ['regulation', 'ban', 'approval', 'etf', 'hack', 'partnership', 'adoption']
        positive_keywords = ['approval', 'adoption', 'partnership', 'bullish', 'positive']
        negative_keywords = ['ban', 'hack', 'crash', 'bearish', 'negative']
        
        # Calculate basic impact score
        impact_score = 0.3  # Base score
        for keyword in high_impact_keywords:
            if keyword in title_lower or keyword in content_lower:
                impact_score += 0.1
        
        impact_score = min(impact_score, 1.0)
        
        # Determine impact type
        positive_count = sum(1 for kw in positive_keywords if kw in title_lower or kw in content_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in title_lower or kw in content_lower)
        
        if positive_count > negative_count:
            impact_type = 'positive'
        elif negative_count > positive_count:
            impact_type = 'negative'
        else:
            impact_type = 'neutral'
        
        # Find mentioned symbols
        affected_symbols = []
        for symbol in self.major_cryptos:
            if symbol.lower() in title_lower or symbol.lower() in content_lower:
                affected_symbols.append(symbol)
        
        if 'bitcoin' in title_lower or 'bitcoin' in content_lower:
            affected_symbols.append('BTC')
        if 'ethereum' in title_lower or 'ethereum' in content_lower:
            affected_symbols.append('ETH')
        
        affected_symbols = list(set(affected_symbols))  # Remove duplicates
        
        return {
            'impact_score': impact_score,
            'time_horizon': 'short-term',
            'affected_symbols': affected_symbols,
            'impact_type': impact_type,
            'confidence': 0.6,
            'urgency_level': 'medium' if impact_score > 0.5 else 'low',
            'market_sectors': ['General'],
            'key_themes': ['News Analysis'],
            'price_prediction': {},
            'actionable_insights': ['Monitor market reaction'],
            'reasoning': content
        }
    
    def validate_impact_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean impact analysis result."""
        # Set defaults and validate ranges
        validated = {
            'impact_score': max(0, min(result.get('impact_score', 0.5), 1.0)),
            'time_horizon': result.get('time_horizon', 'short-term'),
            'affected_symbols': result.get('affected_symbols', []),
            'impact_type': result.get('impact_type', 'neutral'),
            'confidence': max(0, min(result.get('confidence', 0.7), 1.0)),
            'urgency_level': result.get('urgency_level', 'medium'),
            'market_sectors': result.get('market_sectors', []),
            'key_themes': result.get('key_themes', []),
            'price_prediction': result.get('price_prediction', {}),
            'actionable_insights': result.get('actionable_insights', []),
            'reasoning': result.get('reasoning', '')
        }
        
        # Validate enums
        if validated['time_horizon'] not in ['immediate', 'short-term', 'medium-term', 'long-term']:
            validated['time_horizon'] = 'short-term'
        
        if validated['impact_type'] not in ['positive', 'negative', 'neutral']:
            validated['impact_type'] = 'neutral'
        
        if validated['urgency_level'] not in ['low', 'medium', 'high', 'critical']:
            validated['urgency_level'] = 'medium'
        
        # Ensure affected_symbols are valid
        validated['affected_symbols'] = [s for s in validated['affected_symbols'] if isinstance(s, str) and len(s) <= 10]
        
        return validated
    
    def get_default_impact_analysis(self, news_article: Dict) -> Dict[str, Any]:
        """Default impact analysis when LLM fails."""
        return {
            'impact_score': 0.5,
            'time_horizon': 'short-term',
            'affected_symbols': [],
            'impact_type': 'neutral',
            'confidence': 0.5,
            'urgency_level': 'medium',
            'market_sectors': [],
            'key_themes': [],
            'price_prediction': {},
            'actionable_insights': [],
            'reasoning': 'Default analysis due to system error'
        }
    
    async def store_impact_score(self, score: NewsImpactScore):
        """Store news impact score in database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create table if not exists
                create_table_query = """
                CREATE TABLE IF NOT EXISTS news_impact_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    news_id VARCHAR(50) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    title TEXT,
                    content_preview TEXT,
                    impact_score DECIMAL(5,4),
                    time_horizon ENUM('immediate', 'short-term', 'medium-term', 'long-term'),
                    affected_symbols JSON,
                    impact_type ENUM('positive', 'negative', 'neutral'),
                    confidence DECIMAL(5,4),
                    urgency_level ENUM('low', 'medium', 'high', 'critical'),
                    market_sectors JSON,
                    key_themes JSON,
                    price_prediction JSON,
                    llm_reasoning TEXT,
                    actionable_insights JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_news_id (news_id),
                    INDEX idx_impact_score (impact_score),
                    INDEX idx_timestamp (timestamp)
                )
                """
                cursor.execute(create_table_query)
                
                # Insert or update score
                insert_query = """
                INSERT INTO news_impact_scores 
                (news_id, timestamp, title, content_preview, impact_score, time_horizon,
                 affected_symbols, impact_type, confidence, urgency_level, market_sectors,
                 key_themes, price_prediction, llm_reasoning, actionable_insights)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                timestamp = VALUES(timestamp),
                impact_score = VALUES(impact_score),
                time_horizon = VALUES(time_horizon),
                affected_symbols = VALUES(affected_symbols),
                impact_type = VALUES(impact_type),
                confidence = VALUES(confidence),
                urgency_level = VALUES(urgency_level),
                market_sectors = VALUES(market_sectors),
                key_themes = VALUES(key_themes),
                price_prediction = VALUES(price_prediction),
                llm_reasoning = VALUES(llm_reasoning),
                actionable_insights = VALUES(actionable_insights)
                """
                
                cursor.execute(insert_query, (
                    score.news_id,
                    score.timestamp,
                    score.title,
                    score.content_preview,
                    score.impact_score,
                    score.time_horizon,
                    json.dumps(score.affected_symbols),
                    score.impact_type,
                    score.confidence,
                    score.urgency_level,
                    json.dumps(score.market_sectors),
                    json.dumps(score.key_themes),
                    json.dumps(score.price_prediction),
                    score.llm_reasoning[:2000],  # Truncate for storage
                    json.dumps(score.actionable_insights)
                ))
                
                conn.commit()
                logger.info(f"Stored impact score for news {score.news_id}")
                
        except Exception as e:
            logger.error(f"Error storing impact score: {e}")
    
    async def get_recent_impact_scores(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent news impact scores."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT 
                    news_id,
                    timestamp,
                    title,
                    impact_score,
                    time_horizon,
                    affected_symbols,
                    impact_type,
                    confidence,
                    urgency_level,
                    key_themes
                FROM news_impact_scores 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                ORDER BY impact_score DESC, timestamp DESC
                """
                
                cursor.execute(query, (hours,))
                scores = cursor.fetchall()
                
                # Parse JSON fields
                for score in scores:
                    if score['affected_symbols']:
                        score['affected_symbols'] = json.loads(score['affected_symbols'])
                    if score['key_themes']:
                        score['key_themes'] = json.loads(score['key_themes'])
                
                return scores
                
        except Exception as e:
            logger.error(f"Error getting recent impact scores: {e}")
            return []
    
    async def batch_score_recent_news(self, hours: int = 24) -> Dict[str, Any]:
        """Score all recent unprocessed news articles."""
        try:
            # Get unprocessed news
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT n.id, n.title, n.published_date
                FROM crypto_news n
                LEFT JOIN news_impact_scores nis ON n.id = nis.news_id
                WHERE n.published_date >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND nis.news_id IS NULL
                ORDER BY n.published_date DESC
                LIMIT 50
                """
                
                cursor.execute(query, (hours,))
                unprocessed_news = cursor.fetchall()
            
            # Score each article
            results = {
                'processed': 0,
                'high_impact': 0,
                'errors': 0,
                'articles': []
            }
            
            for article in unprocessed_news:
                try:
                    score = await self.score_news_impact(str(article['id']))
                    if score:
                        results['processed'] += 1
                        if score.impact_score >= self.high_impact_threshold:
                            results['high_impact'] += 1
                        
                        results['articles'].append({
                            'news_id': score.news_id,
                            'title': score.title,
                            'impact_score': score.impact_score,
                            'impact_type': score.impact_type,
                            'urgency_level': score.urgency_level
                        })
                    else:
                        results['errors'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing article {article['id']}: {e}")
                    results['errors'] += 1
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch scoring: {e}")
            return {'error': str(e)}
    
    async def generate_market_impact_summary(self) -> Optional[MarketImpactSummary]:
        """Generate market impact summary from recent news."""
        try:
            # Get recent impact scores
            recent_scores = await self.get_recent_impact_scores(hours=24)
            
            if not recent_scores:
                return None
            
            # Calculate summary statistics
            total_articles = len(recent_scores)
            high_impact_articles = sum(1 for s in recent_scores if s['impact_score'] >= self.high_impact_threshold)
            
            # Calculate sentiment
            positive_articles = sum(1 for s in recent_scores if s['impact_type'] == 'positive')
            negative_articles = sum(1 for s in recent_scores if s['impact_type'] == 'negative')
            
            bullish_sentiment = positive_articles / total_articles if total_articles > 0 else 0
            bearish_sentiment = negative_articles / total_articles if total_articles > 0 else 0
            
            # Extract themes and symbols
            all_themes = []
            all_symbols = []
            
            for score in recent_scores:
                if score.get('key_themes'):
                    all_themes.extend(score['key_themes'])
                if score.get('affected_symbols'):
                    all_symbols.extend(score['affected_symbols'])
            
            # Count occurrences
            theme_counts = defaultdict(int)
            symbol_counts = defaultdict(int)
            
            for theme in all_themes:
                theme_counts[theme] += 1
            for symbol in all_symbols:
                symbol_counts[symbol] += 1
            
            # Get top themes and symbols
            top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Determine overall market direction
            if bullish_sentiment > bearish_sentiment + 0.2:
                market_direction = 'bullish'
            elif bearish_sentiment > bullish_sentiment + 0.2:
                market_direction = 'bearish'
            else:
                market_direction = 'mixed'
            
            # Get LLM market outlook
            outlook = await self.get_llm_market_outlook(recent_scores)
            
            summary = MarketImpactSummary(
                timestamp=datetime.now(),
                total_articles=total_articles,
                high_impact_articles=high_impact_articles,
                bullish_sentiment=bullish_sentiment,
                bearish_sentiment=bearish_sentiment,
                top_themes=[theme for theme, count in top_themes],
                most_affected_symbols=[symbol for symbol, count in top_symbols],
                overall_market_direction=market_direction,
                confidence=0.8,  # Would calculate based on article confidence
                llm_market_outlook=outlook
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market impact summary: {e}")
            return None
    
    async def get_llm_market_outlook(self, recent_scores: List[Dict]) -> str:
        """Get LLM-generated market outlook."""
        try:
            # Prepare summary of recent news
            news_summary = f"Recent news analysis ({len(recent_scores)} articles):\n"
            
            for score in recent_scores[:10]:  # Top 10 by impact
                news_summary += f"- {score['title'][:100]}... (Impact: {score['impact_score']:.2f}, {score['impact_type']})\n"
            
            context = f"""
            Based on the following recent cryptocurrency news analysis, provide a market outlook:
            
            {news_summary}
            
            Provide a concise market outlook considering:
            1. Overall sentiment from news
            2. Potential market movements
            3. Key risks and opportunities
            4. Recommended trading approach
            
            Keep response under 200 words.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a crypto market analyst providing concise market outlooks based on news analysis."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting LLM market outlook: {e}")
            return "Market outlook unavailable due to analysis error."
    
    async def get_high_impact_news(self, hours: int = 12) -> List[Dict[str, Any]]:
        """Get high-impact news alerts."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT 
                    news_id,
                    timestamp,
                    title,
                    impact_score,
                    time_horizon,
                    affected_symbols,
                    impact_type,
                    urgency_level,
                    actionable_insights
                FROM news_impact_scores 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                AND impact_score >= %s
                ORDER BY impact_score DESC, timestamp DESC
                """
                
                cursor.execute(query, (hours, self.high_impact_threshold))
                alerts = cursor.fetchall()
                
                # Parse JSON fields
                for alert in alerts:
                    if alert['affected_symbols']:
                        alert['affected_symbols'] = json.loads(alert['affected_symbols'])
                    if alert['actionable_insights']:
                        alert['actionable_insights'] = json.loads(alert['actionable_insights'])
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error getting high impact news: {e}")
            return []

async def main():
    """Main entry point."""
    scorer = NewsImpactScorer()
    
    config = uvicorn.Config(
        scorer.app,
        host="0.0.0.0",
        port=8036,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
