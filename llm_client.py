#!/usr/bin/env python3
"""
LLM Integration Client for Crypto Data Collection
================================================

This service provides clean API integration with your existing aitest Ollama services.
It acts as a bridge between your data collection pipeline and your aitest LLM services.

Architecture:
crypto-data-collection (this) → aitest/Ollama (your existing) → Enhanced Data
"""

import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMIntegrationClient:
    """Integration client for aitest Ollama services"""
    
    def __init__(self):
        # Your existing aitest Ollama endpoints
        self.aitest_ollama_endpoint = os.getenv('AITEST_OLLAMA_ENDPOINT', 
                                               'http://ollama-llm-service.crypto-trading.svc.cluster.local:8050')
        
        self.app = FastAPI(
            title="LLM Integration Client",
            description="Bridge to aitest Ollama services for data enhancement",
            version="1.0.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes as proxy to aitest services"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "llm-integration-client",
                "purpose": "Bridge to aitest Ollama services",
                "target": self.aitest_ollama_endpoint,
                "status": "active"
            }
        
        @self.app.get("/health")
        async def health_check():
            # Check connection to aitest Ollama
            aitest_healthy = await self.test_aitest_connection()
            return {
                "status": "healthy" if aitest_healthy else "degraded",
                "aitest_ollama_connected": aitest_healthy,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/enhance-sentiment")
        async def enhance_sentiment(request: dict):
            """Proxy sentiment enhancement to aitest Ollama"""
            return await self.proxy_to_aitest("enhance-sentiment", request)
        
        @self.app.post("/analyze-narrative")
        async def analyze_narrative(request: dict):
            """Proxy narrative analysis to aitest Ollama"""
            return await self.proxy_to_aitest("analyze-narrative", request)
        
        @self.app.post("/technical-patterns")
        async def analyze_technical_patterns(request: dict):
            """Proxy technical pattern analysis to aitest Ollama"""
            return await self.proxy_to_aitest("technical-patterns", request)
        
        @self.app.get("/models")
        async def list_available_models():
            """List models available in aitest"""
            return await self.proxy_to_aitest("models", {})
    
    async def test_aitest_connection(self) -> bool:
        """Test connection to aitest Ollama service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.aitest_ollama_endpoint}/health", 
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"aitest connection failed: {e}")
            return False
    
    async def proxy_to_aitest(self, endpoint: str, data: dict) -> dict:
        """Proxy requests to aitest Ollama services"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.aitest_ollama_endpoint}/{endpoint}",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"aitest service error: {response.status}"
                        )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="aitest service timeout")
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            raise HTTPException(status_code=502, detail="aitest service unavailable")

# Initialize client
llm_client = LLMIntegrationClient()
app = llm_client.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8040))
    uvicorn.run(app, host="0.0.0.0", port=port)