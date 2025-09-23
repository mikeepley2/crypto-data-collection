"""
Data Collection API Gateway

Unified API for accessing all collected cryptocurrency and financial data.
This gateway provides real-time and historical data access for the trading system
while maintaining complete isolation from data collection processes.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import aioredis
import aiomysql
from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
DATABASE_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql-data-collection"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "data_collector"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "db": os.getenv("MYSQL_DATABASE", "crypto_data_collection"),
    "charset": "utf8mb4",
    "autocommit": True
}

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "redis-data-collection"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", "password"),
    "decode_responses": True
}

# API Configuration
API_CONFIG = {
    "port": int(os.getenv("PORT", "8000")),
    "workers": int(os.getenv("WORKERS", "4")),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
    "rate_limit": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
    "rate_window": int(os.getenv("RATE_LIMIT_WINDOW", "60"))
}

# Security
security = HTTPBearer()
VALID_API_KEYS = {
    os.getenv("API_KEY_MASTER", "master-key"): "master",
    os.getenv("API_KEY_TRADING", "trading-key"): "trading",
    os.getenv("API_KEY_READONLY", "readonly-key"): "readonly"
}

# Global connection pools
mysql_pool = None
redis_client = None

# Data Models
class PriceData(BaseModel):
    symbol: str
    current_price: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: Optional[float] = None
    total_volume: Optional[float] = None
    timestamp: datetime

class SentimentData(BaseModel):
    symbol: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    source: str
    timestamp: datetime

class NewsArticle(BaseModel):
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    symbols: List[str]
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None

class TechnicalIndicators(BaseModel):
    symbol: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    timestamp: datetime

class MLFeatures(BaseModel):
    symbol: str
    features: Dict[str, float]
    timestamp: datetime

class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    components: Dict[str, str]
    metrics: Dict[str, Any]

# Connection Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup database connections"""
    global mysql_pool, redis_client
    
    try:
        # Initialize MySQL pool
        mysql_pool = await aiomysql.create_pool(**DATABASE_CONFIG, maxsize=20)
        logger.info("MySQL connection pool initialized")
        
        # Initialize Redis client
        redis_client = aioredis.from_url(
            f"redis://:{REDIS_CONFIG['password']}@{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/0",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise
    finally:
        # Cleanup connections
        if mysql_pool:
            mysql_pool.close()
            await mysql_pool.wait_closed()
        if redis_client:
            await redis_client.close()
        logger.info("Database connections closed")

# Create FastAPI app
app = FastAPI(
    title="Crypto Data Collection API",
    description="Unified API for cryptocurrency and financial data",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key and return access level"""
    api_key = credentials.credentials
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return VALID_API_KEYS[api_key]

# Database utilities
async def get_mysql_connection():
    """Get MySQL connection from pool"""
    if not mysql_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    return await mysql_pool.acquire()

async def get_redis_client():
    """Get Redis client"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis connection not available")
    return redis_client

# API Routes

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """System health check"""
    components = {}
    metrics = {}
    
    try:
        # Check MySQL
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                components["mysql"] = "healthy"
    except Exception as e:
        components["mysql"] = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis
        await redis_client.ping()
        components["redis"] = "healthy"
    except Exception as e:
        components["redis"] = f"unhealthy: {str(e)}"
    
    # Overall status
    status = "healthy" if all(c == "healthy" for c in components.values()) else "degraded"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        components=components,
        metrics=metrics
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        async with mysql_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
        await redis_client.ping()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

# Price Data Endpoints
@app.get("/api/v1/prices/current/{symbol}", response_model=PriceData)
async def get_current_price(symbol: str, access_level: str = Depends(verify_api_key)):
    """Get current price for a cryptocurrency"""
    
    # Try Redis cache first
    redis = await get_redis_client()
    cache_key = f"price:current:{symbol.upper()}"
    cached_data = await redis.get(cache_key)
    
    if cached_data:
        data = json.loads(cached_data)
        return PriceData(**data)
    
    # Fetch from database
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, current_price, price_change_24h, price_change_percentage_24h,
                   market_cap, total_volume, timestamp
            FROM raw_price_data 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            await cursor.execute(query, (symbol.upper(),))
            result = await cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}")
            
            price_data = PriceData(**result)
            
            # Cache for 1 minute
            await redis.setex(cache_key, 60, json.dumps(result, default=str))
            
            return price_data

@app.get("/api/v1/prices/historical/{symbol}")
async def get_historical_prices(
    symbol: str,
    start: datetime = Query(..., description="Start date"),
    end: datetime = Query(..., description="End date"),
    interval: str = Query("1h", description="Data interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    access_level: str = Depends(verify_api_key)
):
    """Get historical price data"""
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, current_price, price_change_24h, price_change_percentage_24h,
                   market_cap, total_volume, timestamp
            FROM raw_price_data 
            WHERE symbol = %s AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
            """
            await cursor.execute(query, (symbol.upper(), start, end))
            results = await cursor.fetchall()
            
            return [PriceData(**row) for row in results]

# Sentiment Data Endpoints
@app.get("/api/v1/sentiment/crypto/{symbol}", response_model=List[SentimentData])
async def get_crypto_sentiment(
    symbol: str,
    limit: int = Query(10, le=100),
    access_level: str = Depends(verify_api_key)
):
    """Get recent crypto sentiment data"""
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, sentiment_score, sentiment_label, confidence, source, timestamp
            FROM sentiment_analysis_results 
            WHERE symbol = %s AND source = 'crypto'
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            await cursor.execute(query, (symbol.upper(), limit))
            results = await cursor.fetchall()
            
            return [SentimentData(**row) for row in results]

@app.get("/api/v1/sentiment/stock/{symbol}", response_model=List[SentimentData])
async def get_stock_sentiment(
    symbol: str,
    limit: int = Query(10, le=100),
    access_level: str = Depends(verify_api_key)
):
    """Get recent stock sentiment data"""
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, sentiment_score, sentiment_label, confidence, source, timestamp
            FROM sentiment_analysis_results 
            WHERE symbol = %s AND source = 'stock'
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            await cursor.execute(query, (symbol.upper(), limit))
            results = await cursor.fetchall()
            
            return [SentimentData(**row) for row in results]

# News Data Endpoints
@app.get("/api/v1/news/crypto/latest", response_model=List[NewsArticle])
async def get_latest_crypto_news(
    limit: int = Query(20, le=100),
    access_level: str = Depends(verify_api_key)
):
    """Get latest cryptocurrency news"""
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT title, content, source, url, published_at, symbols, 
                   sentiment_score, relevance_score
            FROM crypto_news_articles 
            ORDER BY published_at DESC 
            LIMIT %s
            """
            await cursor.execute(query, (limit,))
            results = await cursor.fetchall()
            
            # Parse symbols JSON
            for row in results:
                if row['symbols']:
                    row['symbols'] = json.loads(row['symbols'])
                else:
                    row['symbols'] = []
            
            return [NewsArticle(**row) for row in results]

# Technical Indicators Endpoints
@app.get("/api/v1/technical/{symbol}/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(
    symbol: str,
    access_level: str = Depends(verify_api_key)
):
    """Get latest technical indicators for a symbol"""
    
    # Try Redis cache first
    redis = await get_redis_client()
    cache_key = f"technical:indicators:{symbol.upper()}"
    cached_data = await redis.get(cache_key)
    
    if cached_data:
        data = json.loads(cached_data)
        return TechnicalIndicators(**data)
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, rsi, macd, macd_signal, bb_upper, bb_middle, bb_lower,
                   sma_20, sma_50, ema_12, ema_26, timestamp
            FROM technical_indicators 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            await cursor.execute(query, (symbol.upper(),))
            result = await cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Technical indicators not found for {symbol}")
            
            indicators = TechnicalIndicators(**result)
            
            # Cache for 5 minutes
            await redis.setex(cache_key, 300, json.dumps(result, default=str))
            
            return indicators

# ML Features Endpoints
@app.get("/api/v1/ml-features/{symbol}/current", response_model=MLFeatures)
async def get_current_ml_features(
    symbol: str,
    access_level: str = Depends(verify_api_key)
):
    """Get current ML features for a symbol"""
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
            SELECT symbol, features, timestamp
            FROM ml_features_materialized 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            await cursor.execute(query, (symbol.upper(),))
            result = await cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"ML features not found for {symbol}")
            
            # Parse features JSON
            result['features'] = json.loads(result['features'])
            
            return MLFeatures(**result)

@app.get("/api/v1/ml-features/bulk")
async def get_bulk_ml_features(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    access_level: str = Depends(verify_api_key)
):
    """Get ML features for multiple symbols"""
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            placeholders = ",".join(["%s"] * len(symbol_list))
            query = f"""
            SELECT symbol, features, timestamp
            FROM ml_features_materialized 
            WHERE symbol IN ({placeholders})
            AND timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY symbol, timestamp DESC
            """
            await cursor.execute(query, symbol_list)
            results = await cursor.fetchall()
            
            # Group by symbol and take latest
            features_by_symbol = {}
            for row in results:
                symbol = row['symbol']
                if symbol not in features_by_symbol:
                    row['features'] = json.loads(row['features'])
                    features_by_symbol[symbol] = MLFeatures(**row)
            
            return features_by_symbol

# WebSocket for real-time data
@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for real-time price updates"""
    await websocket.accept()
    
    try:
        # Get subscription request
        data = await websocket.receive_json()
        symbols = data.get("symbols", [])
        api_key = data.get("api_key")
        
        # Verify API key
        if api_key not in VALID_API_KEYS:
            await websocket.send_json({"error": "Invalid API key"})
            await websocket.close()
            return
        
        # Subscribe to Redis updates
        redis = await get_redis_client()
        pubsub = redis.pubsub()
        
        # Subscribe to price update channels
        for symbol in symbols:
            await pubsub.subscribe(f"price_update:{symbol.upper()}")
        
        # Listen for updates
        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        await pubsub.unsubscribe()

# Statistics and Monitoring
@app.get("/api/v1/stats/collectors")
async def get_collector_stats(access_level: str = Depends(verify_api_key)):
    """Get statistics about data collection"""
    
    stats = {}
    
    async with mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Price data stats
            await cursor.execute("""
                SELECT COUNT(*) as count, MAX(timestamp) as latest 
                FROM raw_price_data 
                WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            result = await cursor.fetchone()
            stats['price_data'] = result
            
            # News stats
            await cursor.execute("""
                SELECT COUNT(*) as count, MAX(published_at) as latest 
                FROM crypto_news_articles 
                WHERE published_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            result = await cursor.fetchone()
            stats['news_articles'] = result
            
            # Sentiment stats
            await cursor.execute("""
                SELECT COUNT(*) as count, MAX(timestamp) as latest 
                FROM sentiment_analysis_results 
                WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            result = await cursor.fetchone()
            stats['sentiment_analysis'] = result
    
    return stats

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_CONFIG["port"],
        workers=API_CONFIG["workers"],
        log_level="info"
    )