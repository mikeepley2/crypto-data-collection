#!/usr/bin/env python3
"""
Enhanced Sentiment Analysis Integration
======================================

This service enhances the existing CryptoBERT sentiment analysis by integrating
with Ollama LLM for deeper emotional and psychological insights.

Integration points:
- Combines CryptoBERT scores with LLM emotional analysis
- Provides market psychology insights
- Enhances confidence scoring
- Generates actionable sentiment intelligence
"""

import os
import json
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedSentimentResult:
    """Enhanced sentiment analysis result"""
    symbol: str
    text: str
    
    # Original CryptoBERT results
    cryptobert_score: float
    cryptobert_confidence: float
    
    # LLM enhancements
    emotional_context: str
    market_psychology: str
    fear_greed_indicator: str
    sentiment_strength: str
    
    # Combined analysis
    enhanced_score: float
    confidence: float
    recommendation: str
    reasoning: str
    
    timestamp: datetime

class EnhancedSentimentService:
    """Enhanced sentiment service integrating CryptoBERT + Ollama"""
    
    def __init__(self):
        # Service endpoints
        self.cryptobert_endpoint = os.getenv('CRYPTOBERT_ENDPOINT', 
                                           'http://sentiment-microservice.crypto-collectors.svc.cluster.local:8080')
        self.ollama_llm_endpoint = os.getenv('OLLAMA_LLM_ENDPOINT',
                                           'http://ollama-llm-service.crypto-collectors.svc.cluster.local:8037')
        
        self.app = FastAPI(
            title="Enhanced Crypto Sentiment Analysis",
            description="CryptoBERT + Ollama LLM sentiment enhancement",
            version="1.0.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "enhanced-sentiment-analysis", 
                "version": "1.0.0",
                "status": "active"
            }
        
        @self.app.get("/health")
        async def health_check():
            # Test connections to dependencies
            cryptobert_healthy = await self.test_service_connection(self.cryptobert_endpoint)
            ollama_healthy = await self.test_service_connection(self.ollama_llm_endpoint)
            
            return {
                "status": "healthy" if cryptobert_healthy and ollama_healthy else "degraded",
                "cryptobert_connected": cryptobert_healthy,
                "ollama_connected": ollama_healthy,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/analyze-sentiment")
        async def analyze_enhanced_sentiment(request: dict):
            """Analyze sentiment using CryptoBERT + Ollama enhancement"""
            text = request.get('text', '')
            symbol = request.get('symbol', 'CRYPTO')
            
            if not text:
                raise HTTPException(status_code=400, detail="Text is required")
            
            result = await self.analyze_enhanced_sentiment(text, symbol)
            return {"result": asdict(result) if result else None}
        
        @self.app.post("/batch-analyze")
        async def batch_analyze_sentiment(request: dict):
            """Batch analyze multiple texts"""
            texts = request.get('texts', [])
            symbol = request.get('symbol', 'CRYPTO')
            
            if not texts:
                raise HTTPException(status_code=400, detail="Texts array is required")
            
            results = []
            for text in texts:
                result = await self.analyze_enhanced_sentiment(text, symbol)
                if result:
                    results.append(asdict(result))
            
            return {"results": results, "count": len(results)}
    
    async def test_service_connection(self, endpoint: str) -> bool:
        """Test connection to a service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False
    
    async def analyze_enhanced_sentiment(self, text: str, symbol: str) -> Optional[EnhancedSentimentResult]:
        """Analyze sentiment using CryptoBERT + Ollama enhancement"""
        try:
            # Step 1: Get CryptoBERT analysis
            cryptobert_result = await self.get_cryptobert_sentiment(text)
            if not cryptobert_result:
                logger.error("Failed to get CryptoBERT sentiment")
                return None
            
            # Step 2: Get Ollama LLM enhancement
            llm_enhancement = await self.get_ollama_enhancement(text, cryptobert_result['score'])
            if not llm_enhancement:
                logger.warning("Failed to get LLM enhancement, using CryptoBERT only")
                llm_enhancement = self.create_fallback_enhancement(cryptobert_result['score'])
            
            # Step 3: Combine results
            enhanced_result = self.combine_sentiment_analysis(
                text, symbol, cryptobert_result, llm_enhancement
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced sentiment analysis error: {e}")
            return None
    
    async def get_cryptobert_sentiment(self, text: str) -> Optional[Dict]:
        """Get sentiment from CryptoBERT service"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"texts": [text]}
                async with session.post(
                    f"{self.cryptobert_endpoint}/sentiment",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Extract the first result
                        if result and len(result) > 0:
                            return {
                                "score": result[0].get("sentiment_score", 0.0),
                                "confidence": result[0].get("confidence", 0.5),
                                "summary": result[0].get("summary", "")
                            }
                    return None
        except Exception as e:
            logger.error(f"CryptoBERT request error: {e}")
            return None
    
    async def get_ollama_enhancement(self, text: str, original_score: float) -> Optional[Dict]:
        """Get LLM enhancement from Ollama service"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "original_score": original_score
                }
                async with session.post(
                    f"{self.ollama_llm_endpoint}/enhance-sentiment",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("result")
                    return None
        except Exception as e:
            logger.error(f"Ollama enhancement request error: {e}")
            return None
    
    def create_fallback_enhancement(self, score: float) -> Dict:
        """Create fallback enhancement when LLM is unavailable"""
        # Simple rule-based enhancement
        if score > 0.5:
            emotion = "confidence"
            psychology = "Bullish market sentiment with positive outlook"
            fear_greed = "greed"
            strength = "strong"
        elif score < -0.5:
            emotion = "fear"
            psychology = "Bearish market sentiment with negative outlook"
            fear_greed = "fear"
            strength = "strong"
        else:
            emotion = "uncertainty"
            psychology = "Neutral market sentiment with mixed signals"
            fear_greed = "uncertainty"
            strength = "moderate"
        
        return {
            "enhanced_emotion": emotion,
            "market_psychology": psychology,
            "confidence": 0.6,
            "reasoning": f"Fallback analysis based on score {score:.2f}"
        }
    
    def combine_sentiment_analysis(
        self, 
        text: str, 
        symbol: str, 
        cryptobert_result: Dict, 
        llm_enhancement: Dict
    ) -> EnhancedSentimentResult:
        """Combine CryptoBERT and LLM results"""
        
        # Calculate enhanced score (weighted combination)
        cryptobert_weight = 0.6
        llm_weight = 0.4
        
        original_score = cryptobert_result["score"]
        llm_confidence = llm_enhancement.get("confidence", 0.5)
        
        # Adjust score based on LLM confidence
        if llm_enhancement.get("enhanced_emotion") == "panic":
            enhanced_score = min(original_score - 0.2, -0.8)
        elif llm_enhancement.get("enhanced_emotion") == "euphoria":
            enhanced_score = max(original_score + 0.2, 0.8)
        else:
            enhanced_score = (cryptobert_weight * original_score + 
                            llm_weight * original_score * llm_confidence)
        
        # Determine fear/greed and strength
        fear_greed = self.determine_fear_greed(enhanced_score, llm_enhancement)
        strength = self.determine_strength(enhanced_score, llm_confidence)
        
        # Generate recommendation
        recommendation = self.generate_recommendation(enhanced_score, fear_greed, strength)
        
        # Combine confidence scores
        combined_confidence = (cryptobert_result["confidence"] + llm_confidence) / 2
        
        return EnhancedSentimentResult(
            symbol=symbol,
            text=text[:200] + "..." if len(text) > 200 else text,
            
            # Original CryptoBERT
            cryptobert_score=original_score,
            cryptobert_confidence=cryptobert_result["confidence"],
            
            # LLM enhancements
            emotional_context=llm_enhancement.get("enhanced_emotion", "neutral"),
            market_psychology=llm_enhancement.get("market_psychology", "Mixed signals"),
            fear_greed_indicator=fear_greed,
            sentiment_strength=strength,
            
            # Combined analysis
            enhanced_score=enhanced_score,
            confidence=combined_confidence,
            recommendation=recommendation,
            reasoning=llm_enhancement.get("reasoning", "Combined CryptoBERT and LLM analysis"),
            
            timestamp=datetime.now()
        )
    
    def determine_fear_greed(self, score: float, llm_enhancement: Dict) -> str:
        """Determine fear/greed indicator"""
        emotion = llm_enhancement.get("enhanced_emotion", "")
        
        if emotion in ["panic", "fear"]:
            return "extreme_fear"
        elif emotion in ["euphoria", "greed"]:
            return "extreme_greed"
        elif score > 0.3:
            return "greed"
        elif score < -0.3:
            return "fear"
        else:
            return "neutral"
    
    def determine_strength(self, score: float, confidence: float) -> str:
        """Determine sentiment strength"""
        magnitude = abs(score)
        
        if magnitude > 0.7 and confidence > 0.8:
            return "very_strong"
        elif magnitude > 0.5 and confidence > 0.6:
            return "strong"
        elif magnitude > 0.3:
            return "moderate"
        else:
            return "weak"
    
    def generate_recommendation(self, score: float, fear_greed: str, strength: str) -> str:
        """Generate trading recommendation"""
        if strength in ["very_strong", "strong"]:
            if score > 0.5:
                return "Strong bullish sentiment - Consider long positions"
            elif score < -0.5:
                return "Strong bearish sentiment - Consider short positions or exit longs"
        
        if fear_greed == "extreme_fear":
            return "Extreme fear detected - Potential buying opportunity"
        elif fear_greed == "extreme_greed":
            return "Extreme greed detected - Consider profit taking"
        
        return "Mixed sentiment - Wait for clearer signals"

# Request models
class SentimentRequest(BaseModel):
    text: str
    symbol: str = "CRYPTO"

class BatchSentimentRequest(BaseModel):
    texts: List[str]
    symbol: str = "CRYPTO"

# Initialize service
enhanced_sentiment = EnhancedSentimentService()
app = enhanced_sentiment.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8038))
    uvicorn.run(app, host="0.0.0.0", port=port)