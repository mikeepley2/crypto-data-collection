#!/usr/bin/env python3
"""
Ollama LLM Service for Crypto Data Enhancement
==============================================

This service provides LLM-powered analysis using local Ollama models for:
- Enhanced sentiment analysis
- Market narrative extraction  
- Technical pattern recognition
- Market regime classification
- Cross-asset correlation analysis

Integrates with existing crypto data collection pipeline.
"""

import os
import sys
import json
import logging
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNCERTAINTY = "uncertainty"

class SentimentEnhancement(Enum):
    """Enhanced sentiment types"""
    FEAR = "fear"
    GREED = "greed"
    EUPHORIA = "euphoria"
    PANIC = "panic"
    UNCERTAINTY = "uncertainty"
    CONFIDENCE = "confidence"

@dataclass
class EnhancedSentimentResult:
    """Enhanced sentiment analysis result"""
    original_score: float
    enhanced_emotion: SentimentEnhancement
    market_psychology: str
    confidence: float
    reasoning: str
    timestamp: datetime

@dataclass
class MarketNarrative:
    """Market narrative extraction result"""
    primary_theme: str
    secondary_themes: List[str]
    market_impact: str
    affected_assets: List[str]
    timeline: str
    confidence: float
    reasoning: str

@dataclass
class TechnicalPattern:
    """Technical pattern recognition result"""
    pattern_name: str
    pattern_type: str
    confidence: float
    timeframe: str
    price_target: Optional[float]
    stop_loss: Optional[float]
    market_context: str
    reasoning: str

class OllamaLLMService:
    """Ollama LLM service for crypto data enhancement"""
    
    def __init__(self):
        self.ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://ollama:11434')
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'host.docker.internal'),
            'user': os.getenv('MYSQL_USER', 'news_collector'),
            'password': os.getenv('MYSQL_PASSWORD', '99Rules!'),
            'database': os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            'charset': 'utf8mb4'
        }
        
        # Model configurations for different tasks
        self.models = {
            'sentiment': os.getenv('OLLAMA_SENTIMENT_MODEL', 'llama3.2:3b'),
            'narrative': os.getenv('OLLAMA_NARRATIVE_MODEL', 'mistral:7b'),
            'technical': os.getenv('OLLAMA_TECHNICAL_MODEL', 'deepseek-coder:6.7b'),
            'regime': os.getenv('OLLAMA_REGIME_MODEL', 'qwen2.5:7b')
        }
        
        self.app = FastAPI(
            title="Ollama LLM Crypto Enhancement Service",
            description="Advanced LLM analysis for crypto data",
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
            
    async def ollama_request(self, model: str, prompt: str, system: str = None) -> Optional[str]:
        """Make request to Ollama API"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            if system:
                payload["system"] = system
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        logger.error(f"Ollama request failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return None
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {"service": "ollama-llm-crypto", "version": "1.0.0", "status": "active"}
        
        @self.app.get("/health")
        async def health_check():
            # Test Ollama connection
            ollama_healthy = await self.test_ollama_connection()
            
            # Test database connection
            db_healthy = self.get_connection() is not None
            
            return {
                "status": "healthy" if ollama_healthy and db_healthy else "degraded",
                "ollama_connected": ollama_healthy,
                "database_connected": db_healthy,
                "models": self.models,
                "timestamp": datetime.now().isoformat()
            }
            
        @self.app.get("/models")
        async def list_models():
            """List available Ollama models"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.ollama_endpoint}/api/tags") as response:
                        if response.status == 200:
                            result = await response.json()
                            return {"models": result.get('models', []), "configured": self.models}
                        return {"error": "Could not fetch models"}
            except Exception as e:
                return {"error": str(e)}
        
        @self.app.post("/enhance-sentiment")
        async def enhance_sentiment(request: dict):
            """Enhance sentiment analysis with emotional context"""
            text = request.get('text', '')
            original_score = request.get('original_score', 0.0)
            
            if not text:
                raise HTTPException(status_code=400, detail="Text is required")
                
            result = await self.enhance_sentiment_analysis(text, original_score)
            return {"result": asdict(result) if result else None}
        
        @self.app.post("/extract-narrative")
        async def extract_market_narrative(request: dict):
            """Extract market narrative from news/text"""
            text = request.get('text', '')
            
            if not text:
                raise HTTPException(status_code=400, detail="Text is required")
                
            result = await self.extract_market_narrative(text)
            return {"result": asdict(result) if result else None}
        
        @self.app.post("/analyze-technical-pattern")
        async def analyze_technical_pattern(request: dict):
            """Analyze technical patterns from price data"""
            symbol = request.get('symbol', '')
            timeframe = request.get('timeframe', '1h')
            
            if not symbol:
                raise HTTPException(status_code=400, detail="Symbol is required")
                
            result = await self.analyze_technical_pattern(symbol, timeframe)
            return {"result": asdict(result) if result else None}
        
        @self.app.post("/classify-market-regime")
        async def classify_market_regime(request: dict):
            """Classify current market regime"""
            symbols = request.get('symbols', ['BTC', 'ETH'])
            lookback_days = request.get('lookback_days', 30)
            
            result = await self.classify_market_regime(symbols, lookback_days)
            return {"result": result}
    
    async def test_ollama_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_endpoint}/api/tags") as response:
                    return response.status == 200
        except:
            return False
    
    async def enhance_sentiment_analysis(self, text: str, original_score: float) -> Optional[EnhancedSentimentResult]:
        """Enhance sentiment with emotional and psychological context"""
        system_prompt = """You are an expert crypto market psychologist. Analyze the emotional and psychological aspects of market sentiment.
        
        Your task:
        1. Identify the underlying emotions (fear, greed, euphoria, panic, uncertainty, confidence)
        2. Analyze market psychology patterns
        3. Assess confidence in the sentiment
        4. Provide clear reasoning
        
        Return JSON format:
        {
            "enhanced_emotion": "emotion_type",
            "market_psychology": "psychological analysis",
            "confidence": 0.85,
            "reasoning": "detailed explanation"
        }"""
        
        prompt = f"""Analyze this crypto-related text for enhanced sentiment:
        
        Text: "{text}"
        Original sentiment score: {original_score} (range -1 to 1)
        
        Provide enhanced emotional analysis focusing on market psychology."""
        
        try:
            response = await self.ollama_request(self.models['sentiment'], prompt, system_prompt)
            if response:
                # Parse JSON response
                result_data = json.loads(response)
                return EnhancedSentimentResult(
                    original_score=original_score,
                    enhanced_emotion=SentimentEnhancement(result_data['enhanced_emotion']),
                    market_psychology=result_data['market_psychology'],
                    confidence=result_data['confidence'],
                    reasoning=result_data['reasoning'],
                    timestamp=datetime.now()
                )
        except Exception as e:
            logger.error(f"Sentiment enhancement error: {e}")
            return None
    
    async def extract_market_narrative(self, text: str) -> Optional[MarketNarrative]:
        """Extract market narrative and themes"""
        system_prompt = """You are a crypto market analyst specializing in narrative extraction. Identify:
        
        1. Primary market theme (regulation, adoption, technology, macro, etc.)
        2. Secondary themes
        3. Market impact assessment
        4. Affected crypto assets
        5. Timeline implications
        
        Return JSON format:
        {
            "primary_theme": "main theme",
            "secondary_themes": ["theme1", "theme2"],
            "market_impact": "impact description",
            "affected_assets": ["BTC", "ETH"],
            "timeline": "short-term/medium-term/long-term",
            "confidence": 0.85,
            "reasoning": "explanation"
        }"""
        
        prompt = f"""Extract market narrative from this crypto news/text:
        
        Text: "{text}"
        
        Focus on identifying market-moving themes and their implications."""
        
        try:
            response = await self.ollama_request(self.models['narrative'], prompt, system_prompt)
            if response:
                result_data = json.loads(response)
                return MarketNarrative(
                    primary_theme=result_data['primary_theme'],
                    secondary_themes=result_data['secondary_themes'],
                    market_impact=result_data['market_impact'],
                    affected_assets=result_data['affected_assets'],
                    timeline=result_data['timeline'],
                    confidence=result_data['confidence'],
                    reasoning=result_data['reasoning']
                )
        except Exception as e:
            logger.error(f"Narrative extraction error: {e}")
            return None
    
    async def analyze_technical_pattern(self, symbol: str, timeframe: str) -> Optional[TechnicalPattern]:
        """Analyze technical patterns using LLM"""
        # Fetch recent price data
        price_data = await self.get_price_data(symbol, timeframe, 50)
        if not price_data:
            return None
            
        system_prompt = """You are a technical analysis expert. Analyze price patterns and provide:
        
        1. Pattern identification (support/resistance, triangles, flags, etc.)
        2. Pattern type (continuation, reversal, consolidation)
        3. Confidence level
        4. Price targets and stop losses
        5. Market context
        
        Return JSON format:
        {
            "pattern_name": "pattern name",
            "pattern_type": "continuation/reversal/consolidation",
            "confidence": 0.75,
            "price_target": 45000.0,
            "stop_loss": 40000.0,
            "market_context": "context description",
            "reasoning": "technical analysis"
        }"""
        
        # Format price data for LLM
        price_summary = self.format_price_data_for_llm(price_data, symbol)
        
        prompt = f"""Analyze technical patterns for {symbol} on {timeframe} timeframe:
        
        {price_summary}
        
        Identify any significant patterns and provide trading insights."""
        
        try:
            response = await self.ollama_request(self.models['technical'], prompt, system_prompt)
            if response:
                result_data = json.loads(response)
                return TechnicalPattern(
                    pattern_name=result_data['pattern_name'],
                    pattern_type=result_data['pattern_type'],
                    confidence=result_data['confidence'],
                    timeframe=timeframe,
                    price_target=result_data.get('price_target'),
                    stop_loss=result_data.get('stop_loss'),
                    market_context=result_data['market_context'],
                    reasoning=result_data['reasoning']
                )
        except Exception as e:
            logger.error(f"Technical pattern analysis error: {e}")
            return None
    
    async def classify_market_regime(self, symbols: List[str], lookback_days: int) -> Optional[Dict]:
        """Classify current market regime"""
        # Get market data for regime analysis
        market_data = {}
        for symbol in symbols:
            data = await self.get_price_data(symbol, '1d', lookback_days)
            if data:
                market_data[symbol] = data
        
        if not market_data:
            return None
            
        system_prompt = """You are a market regime analyst. Classify the current market regime based on:
        
        1. Volatility patterns
        2. Trend direction and strength
        3. Volume patterns
        4. Price momentum
        
        Market regimes: bull_trend, bear_trend, sideways, high_volatility, low_volatility, uncertainty
        
        Return JSON format:
        {
            "regime": "regime_type",
            "confidence": 0.85,
            "characteristics": ["high volatility", "trending up"],
            "duration_estimate": "2-4 weeks",
            "key_drivers": ["adoption news", "institutional interest"],
            "reasoning": "detailed analysis"
        }"""
        
        # Format market data for LLM
        market_summary = self.format_market_data_for_llm(market_data)
        
        prompt = f"""Analyze the current crypto market regime:
        
        {market_summary}
        
        Consider volatility, trends, and overall market behavior."""
        
        try:
            response = await self.ollama_request(self.models['regime'], prompt, system_prompt)
            if response:
                return json.loads(response)
        except Exception as e:
            logger.error(f"Market regime classification error: {e}")
            return None
    
    async def get_price_data(self, symbol: str, timeframe: str, limit: int) -> Optional[List[Dict]]:
        """Get price data from database"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor(dictionary=True)
            
            # Get recent price data
            query = """
            SELECT timestamp_iso, current_price, volume_24h, 
                   price_change_percentage_24h, rsi_14, atr_14
            FROM ml_features_materialized 
            WHERE symbol = %s 
            ORDER BY timestamp_iso DESC 
            LIMIT %s
            """
            
            cursor.execute(query, (symbol, limit))
            data = cursor.fetchall()
            
            conn.close()
            return data
            
        except Exception as e:
            logger.error(f"Error getting price data: {e}")
            return None
    
    def format_price_data_for_llm(self, data: List[Dict], symbol: str) -> str:
        """Format price data for LLM analysis"""
        if not data:
            return ""
            
        recent = data[:10]  # Most recent 10 data points
        
        summary = f"Recent price data for {symbol}:\n"
        for i, point in enumerate(recent):
            summary += f"{i+1}. {point['timestamp_iso']}: "
            summary += f"Price: ${point['current_price']:.2f}, "
            summary += f"Change: {point['price_change_percentage_24h']:.2f}%, "
            summary += f"RSI: {point['rsi_14']:.1f}, "
            summary += f"ATR: {point['atr_14']:.2f}\n"
            
        return summary
    
    def format_market_data_for_llm(self, market_data: Dict) -> str:
        """Format market data for regime analysis"""
        summary = "Market Data Summary:\n"
        
        for symbol, data in market_data.items():
            if data:
                recent = data[:5]  # Last 5 days
                summary += f"\n{symbol}:\n"
                for point in recent:
                    summary += f"  {point['timestamp_iso']}: ${point['current_price']:.2f} "
                    summary += f"({point['price_change_percentage_24h']:+.2f}%)\n"
        
        return summary

# Request/Response models
class SentimentRequest(BaseModel):
    text: str
    original_score: float = Field(..., ge=-1, le=1)

class NarrativeRequest(BaseModel):
    text: str

class TechnicalRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"

class RegimeRequest(BaseModel):
    symbols: List[str] = ["BTC", "ETH"]
    lookback_days: int = 30

# Initialize service
llm_service = OllamaLLMService()
app = llm_service.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8037))
    uvicorn.run(app, host="0.0.0.0", port=port)