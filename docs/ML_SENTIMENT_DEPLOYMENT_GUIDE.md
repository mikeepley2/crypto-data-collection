# ML Sentiment Analysis Deployment Guide

## Overview

This guide documents the complete process for deploying ML-based sentiment analysis services using FinBERT and CryptoBERT models in a Kubernetes cluster. This approach bypasses common issues with Kind clusters and image loading.

## Prerequisites

- Kubernetes cluster (tested with Kind)
- Docker installed locally
- kubectl configured
- Access to the crypto-data-collection namespace

## Architecture

The ML sentiment analysis system consists of:
- **FinBERT**: Specialized model for stock market sentiment analysis
- **CryptoBERT**: Specialized model for cryptocurrency sentiment analysis
- **Enhanced Sentiment Collector**: Kubernetes deployment that loads models at runtime

## Deployment Process

### Step 1: Create ML Sentiment Code

Create the enhanced ML sentiment analysis service:

```bash
# Create the ML sentiment service code
cat > docker/sentiment-services/enhanced_ml_sentiment.py << 'EOF'
#!/usr/bin/env python3
"""
Enhanced ML-based Sentiment Analysis Service

This service provides advanced sentiment analysis using specialized ML models
(FinBERT for stock market, CryptoBERT for crypto) for both crypto and stock
market news, with separate sentiment tracking for each market type.
"""

import os
import sys
import logging
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import mysql.connector
from mysql.connector import pooling
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced_ml_sentiment")

# FastAPI models
class SentimentRequest(BaseModel):
    article_id: Optional[int] = None
    text: Optional[str] = None
    market_type: Optional[str] = None  # 'crypto' or 'stock'

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    crypto_model_loaded: bool
    stock_model_loaded: bool
    database_connected: bool

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced ML Sentiment Analysis",
    description="Advanced sentiment analysis using specialized ML models for crypto and stock market news",
    version="3.0.0",
)

# Database connection pool
db_pool = None

# ML Models
crypto_sentiment_pipeline = None
stock_sentiment_pipeline = None

def init_database_pool():
    """Initialize database connection pool"""
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="sentiment_pool",
            pool_size=5,
            pool_reset_session=True,
            host=os.getenv("MYSQL_HOST", "host.docker.internal"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "news_collector"),
            password=os.getenv("MYSQL_PASSWORD", "99Rules!"),
            database=os.getenv("MYSQL_DATABASE", "crypto_prices"),
            autocommit=True,
        )
        logger.info("✅ Database connection pool initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Database pool initialization failed: {e}")
        return False

def get_db_connection():
    """Get database connection from pool"""
    try:
        return db_pool.get_connection()
    except Exception as e:
        logger.error(f"❌ Failed to get database connection: {e}")
        return None

def load_ml_models():
    """Load specialized ML models for sentiment analysis"""
    global crypto_sentiment_pipeline, stock_sentiment_pipeline

    try:
        logger.info("🔄 Loading CryptoBERT model for crypto sentiment analysis...")
        crypto_sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="kk08/CryptoBERT",
            tokenizer="kk08/CryptoBERT",
            device=-1,  # Force CPU usage
            return_all_scores=True,
        )
        logger.info("✅ CryptoBERT model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load CryptoBERT model: {e}")
        crypto_sentiment_pipeline = None

    try:
        logger.info("🔄 Loading FinBERT model for stock sentiment analysis...")
        stock_sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=-1,  # Force CPU usage
            return_all_scores=True,
        )
        logger.info("✅ FinBERT model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load FinBERT model: {e}")
        stock_sentiment_pipeline = None

def detect_market_type(text: str) -> str:
    """
    Detect if the text is about crypto or stock market

    Args:
        text: The text to analyze

    Returns:
        'crypto' or 'stock'
    """
    text_lower = text.lower()

    # Crypto keywords
    crypto_keywords = [
        "bitcoin", "btc", "ethereum", "eth", "cryptocurrency", "crypto",
        "blockchain", "altcoin", "defi", "nft", "mining", "wallet",
        "exchange", "binance", "coinbase", "dogecoin", "doge", "solana",
        "sol", "cardano", "ada", "polkadot", "dot", "chainlink", "link",
        "uniswap", "pancakeswap", "yield farming", "staking", "metamask",
        "ledger", "trezor", "hodl", "diamond hands", "moon", "pump",
        "dump", "fud", "fomo", "rekt", "rug pull", "whale", "bullish", "bearish"
    ]

    # Stock market keywords
    stock_keywords = [
        "stock", "stocks", "equity", "equities", "nasdaq", "nyse", "s&p",
        "dow jones", "trading", "investor", "portfolio", "dividend",
        "earnings", "revenue", "profit", "market cap", "pe ratio", "analyst",
        "upgrade", "downgrade", "buy", "sell", "hold", "bull market",
        "bear market", "recession", "inflation", "fed", "federal reserve",
        "interest rate", "bond", "bonds", "treasury", "etf", "mutual fund",
        "hedge fund"
    ]

    # Count keyword matches
    crypto_count = sum(1 for keyword in crypto_keywords if keyword in text_lower)
    stock_count = sum(1 for keyword in stock_keywords if keyword in text_lower)

    # Determine market type based on keyword density
    if crypto_count > stock_count:
        return "crypto"
    elif stock_count > crypto_count:
        return "stock"
    else:
        # If equal or no matches, default to crypto for this system
        return "crypto"

def analyze_sentiment_with_ml(text: str, market_type: str) -> Tuple[float, float, str]:
    """
    Analyze sentiment using specialized ML models

    Args:
        text: The text to analyze
        market_type: 'crypto' or 'stock'

    Returns:
        Tuple of (sentiment_score, confidence, analysis_text)
    """
    try:
        # Select appropriate model based on market type
        if market_type == "crypto" and crypto_sentiment_pipeline:
            pipeline = crypto_sentiment_pipeline
            model_name = "CryptoBERT"
        elif market_type == "stock" and stock_sentiment_pipeline:
            pipeline = stock_sentiment_pipeline
            model_name = "FinBERT"
        else:
            # Fallback to available model
            if crypto_sentiment_pipeline:
                pipeline = crypto_sentiment_pipeline
                model_name = "CryptoBERT (fallback)"
            elif stock_sentiment_pipeline:
                pipeline = stock_sentiment_pipeline
                model_name = "FinBERT (fallback)"
            else:
                raise Exception("No ML models available")

        # Truncate text to model's max length (typically 512 tokens)
        max_length = 512
        if len(text) > max_length * 4:  # Rough estimate: 4 chars per token
            text = text[: max_length * 4]

        # Analyze sentiment
        results = pipeline(text)

        # Extract sentiment scores
        if isinstance(results, list) and len(results) > 0:
            # Handle multiple scores format
            scores = {}
            for result in results:
                label = result["label"].lower()
                score = result["score"]
                scores[label] = score

            # Convert to sentiment score (-1 to 1)
            if "positive" in scores and "negative" in scores:
                sentiment_score = scores["positive"] - scores["negative"]
            elif "positive" in scores:
                sentiment_score = scores["positive"]
            elif "negative" in scores:
                sentiment_score = -scores["negative"]
            else:
                # Handle other label formats
                sentiment_score = 0.0

            # Calculate confidence as max score
            confidence = max(scores.values()) if scores else 0.5

            # Create analysis text
            analysis = f"Analyzed using {model_name}: {max(scores, key=scores.get)} sentiment"

        else:
            # Handle single result format
            result = results[0] if isinstance(results, list) else results
            label = result["label"].lower()
            score = result["score"]

            # Convert to sentiment score
            if "positive" in label:
                sentiment_score = score
            elif "negative" in label:
                sentiment_score = -score
            else:
                sentiment_score = 0.0

            confidence = score
            analysis = f"Analyzed using {model_name}: {label} sentiment"

        # Ensure score is in [-1, 1] range
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        # Ensure confidence is in [0, 1] range
        confidence = max(0.0, min(1.0, confidence))

        logger.info(f"🤖 {model_name} sentiment analysis: {sentiment_score:.3f} (confidence: {confidence:.3f})")
        return sentiment_score, confidence, analysis

    except Exception as e:
        logger.error(f"❌ ML sentiment analysis failed: {e}")
        raise Exception(f"ML sentiment analysis failed: {e}")

# FastAPI endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    database_connected = db_pool is not None

    return HealthResponse(
        status=(
            "healthy"
            if database_connected
            and crypto_sentiment_pipeline
            and stock_sentiment_pipeline
            else "degraded"
        ),
        timestamp=datetime.utcnow().isoformat(),
        crypto_model_loaded=crypto_sentiment_pipeline is not None,
        stock_model_loaded=stock_sentiment_pipeline is not None,
        database_connected=database_connected,
    )

@app.get("/status")
async def get_status():
    """Get detailed service status"""
    conn = get_db_connection()
    db_connected = conn is not None
    if conn:
        conn.close()

    return {
        "service": "enhanced_ml_sentiment",
        "version": "3.0.0",
        "status": (
            "operational"
            if db_connected and crypto_sentiment_pipeline and stock_sentiment_pipeline
            else "degraded"
        ),
        "crypto_model_loaded": crypto_sentiment_pipeline is not None,
        "stock_model_loaded": stock_sentiment_pipeline is not None,
        "database_connected": db_connected,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """Analyze sentiment for given text or article"""
    try:
        if request.article_id:
            # Process specific article
            conn = get_db_connection()
            if not conn:
                raise HTTPException(
                    status_code=500, detail="Database connection failed"
                )

            # Get article data
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, title, content, market_type, ml_sentiment_score, ml_sentiment_confidence
                FROM crypto_news
                WHERE id = %s
            """,
                (request.article_id,),
            )

            article = cursor.fetchone()
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")

            # Skip if already processed
            if (
                article["ml_sentiment_score"] is not None
                and article["ml_sentiment_score"] != 0
            ):
                return {"status": "already_processed", "article_id": request.article_id}

            # Combine title and content for analysis
            text = f"{article['title']}"
            if article["content"]:
                text += f" {article['content']}"

            # Detect market type if not set
            market_type = article["market_type"] or detect_market_type(text)

            # Analyze sentiment with ML
            ml_score, ml_confidence, ml_analysis = analyze_sentiment_with_ml(
                text, market_type
            )

            # Update database
            cursor.execute(
                """
                UPDATE crypto_news
                SET ml_sentiment_score = %s,
                    ml_sentiment_confidence = %s,
                    ml_sentiment_analysis = %s,
                    market_type = %s,
                    sentiment_updated_at = NOW()
                WHERE id = %s
            """,
                (
                    ml_score,
                    ml_confidence,
                    ml_analysis,
                    market_type,
                    request.article_id,
                ),
            )

            conn.close()
            return {"status": "success", "article_id": request.article_id, "sentiment_score": ml_score}

        elif request.text:
            # Analyze provided text
            market_type = request.market_type or detect_market_type(request.text)
            score, confidence, analysis = analyze_sentiment_with_ml(
                request.text, market_type
            )

            return {
                "status": "success",
                "market_type": market_type,
                "sentiment_score": score,
                "confidence": confidence,
                "analysis": analysis,
            }

        else:
            raise HTTPException(
                status_code=400, detail="Either article_id or text must be provided"
            )

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "enhanced-ml-sentiment",
        "version": "3.0.0",
        "status": "running",
        "models": {
            "crypto": "CryptoBERT" if crypto_sentiment_pipeline else "Not loaded",
            "stock": "FinBERT" if stock_sentiment_pipeline else "Not loaded",
        },
        "endpoints": {
            "health": "/health",
            "sentiment": "/sentiment",
            "docs": "/docs",
        },
    }

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("🚀 Starting Enhanced ML Sentiment Analysis Service")

    # Initialize database pool
    if not init_database_pool():
        logger.error("❌ Failed to initialize database pool")

    # Load ML models
    load_ml_models()

    logger.info("✅ Enhanced ML Sentiment Analysis Service started")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF
```

### Step 2: Create ConfigMap

Create a ConfigMap with the ML sentiment code:

```bash
kubectl create configmap enhanced-sentiment-ml-code \
  --from-file=enhanced_ml_sentiment.py=docker/sentiment-services/enhanced_ml_sentiment.py \
  -n crypto-data-collection
```

### Step 3: Create Deployment

Create the deployment configuration:

```bash
cat > k8s/collectors/enhanced-sentiment-collector-ml-update.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: enhanced-sentiment-collector
  namespace: crypto-data-collection
spec:
  template:
    spec:
      containers:
        - name: enhanced-sentiment-collector
          args:
            - |
              apt-get update && apt-get install -y gcc g++ && \
              pip install fastapi uvicorn aiohttp mysql-connector-python asyncio torch transformers numpy && \
              python /app/sentiment.py
          volumeMounts:
            - mountPath: /app/sentiment.py
              name: sentiment-code
              subPath: enhanced_ml_sentiment.py
      volumes:
        - name: sentiment-code
          configMap:
            name: enhanced-sentiment-ml-code
EOF
```

### Step 4: Deploy the Service

Apply the deployment:

```bash
kubectl patch deployment enhanced-sentiment-collector -n crypto-data-collection --patch-file k8s/collectors/enhanced-sentiment-collector-ml-update.yaml
```

### Step 5: Monitor Installation

Monitor the installation progress:

```bash
# Check pod status
kubectl get pods -n crypto-data-collection -l app=enhanced-sentiment-collector

# Check installation logs
kubectl logs -f deployment/enhanced-sentiment-collector -n crypto-data-collection
```

## Installation Timeline

The installation process typically takes 10-15 minutes and follows this timeline:

1. **System Dependencies (2-3 minutes)**: Installing gcc, g++, and build tools
2. **Python Base Packages (1-2 minutes)**: FastAPI, uvicorn, aiohttp, mysql-connector-python
3. **PyTorch Installation (5-8 minutes)**: Large download (~900MB) including CUDA dependencies
4. **Transformers Library (1-2 minutes)**: Hugging Face transformers library
5. **Model Download (2-3 minutes)**: FinBERT and CryptoBERT models
6. **Service Startup (30 seconds)**: FastAPI service initialization

## Troubleshooting

### Common Issues

1. **Package Installation Fails**
   - **Problem**: `ERROR: Could not find a version that satisfies the requirement fastapi`
   - **Solution**: Remove PyTorch-specific index URLs from pip install command
   - **Fix**: Use `pip install fastapi uvicorn aiohttp mysql-connector-python asyncio torch transformers numpy` (without `--index-url`)

2. **Pod Restarts During Installation**
   - **Problem**: Pod keeps restarting during dependency installation
   - **Solution**: This is normal during the installation process. Monitor logs to ensure progress continues.

3. **Memory Issues**
   - **Problem**: Pod runs out of memory during model loading
   - **Solution**: Ensure sufficient memory limits (minimum 2Gi recommended)

4. **Model Loading Fails**
   - **Problem**: Models fail to load due to network issues
   - **Solution**: Check internet connectivity and Hugging Face model availability

### Monitoring Commands

```bash
# Check pod status
kubectl get pods -n crypto-data-collection -l app=enhanced-sentiment-collector

# Check logs
kubectl logs -f deployment/enhanced-sentiment-collector -n crypto-data-collection

# Check service health
kubectl port-forward svc/enhanced-sentiment-collector 8000:8000 -n crypto-data-collection
curl http://localhost:8000/health

# Check model status
curl http://localhost:8000/status
```

## Testing the Service

Once the service is running, test it:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test sentiment analysis
curl -X POST "http://localhost:8000/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bitcoin is going to the moon!", "market_type": "crypto"}'

# Test with article ID
curl -X POST "http://localhost:8000/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 12345}'
```

## Performance Considerations

- **Memory Usage**: Each model requires ~1-2GB of RAM
- **CPU Usage**: Model inference is CPU-intensive
- **Startup Time**: Initial model loading takes 2-3 minutes
- **Inference Speed**: ~100-500ms per article depending on text length

## Model Information

- **CryptoBERT**: `kk08/CryptoBERT` - Specialized for cryptocurrency sentiment
- **FinBERT**: `ProsusAI/finbert` - Specialized for financial/stock market sentiment
- **Device**: CPU-only (`device=-1`) to avoid GPU dependencies
- **Max Text Length**: 512 tokens (approximately 2000 characters)

## Database Schema

The service expects the following columns in the `crypto_news` table:

```sql
ALTER TABLE crypto_news ADD COLUMN ml_sentiment_score DECIMAL(3,2);
ALTER TABLE crypto_news ADD COLUMN ml_sentiment_confidence DECIMAL(3,2);
ALTER TABLE crypto_news ADD COLUMN ml_sentiment_analysis TEXT;
ALTER TABLE crypto_news ADD COLUMN market_type VARCHAR(20);
ALTER TABLE crypto_news ADD COLUMN sentiment_updated_at TIMESTAMP;
```

## Maintenance

### Updating Models

To update the models, restart the deployment:

```bash
kubectl rollout restart deployment enhanced-sentiment-collector -n crypto-data-collection
```

### Scaling

To scale the service:

```bash
kubectl scale deployment enhanced-sentiment-collector --replicas=2 -n crypto-data-collection
```

### Resource Monitoring

Monitor resource usage:

```bash
kubectl top pods -n crypto-data-collection -l app=enhanced-sentiment-collector
```

## Best Practices

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Health Checks**: Use readiness and liveness probes
3. **Monitoring**: Monitor model loading and inference performance
4. **Backup**: Keep the working collector as a backup during updates
5. **Testing**: Always test the service after deployment

## Conclusion

This deployment approach provides a reliable way to deploy ML sentiment analysis services in Kubernetes without the complexity of pre-built images or Kind cluster image loading issues. The runtime installation approach ensures compatibility and allows for easy updates and maintenance.


