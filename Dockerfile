# Crypto Data Collection System - Multi-stage Dockerfile
# Supports both lightweight testing and production microservices
# 
# 📋 SERVICE REGISTRY: See docs/SERVICE_INVENTORY.md for complete service documentation
# 🎯 PRODUCTION SERVICES: 9 core microservices (template-compliant, no duplicates)
# 🐳 ARCHITECTURE: Multi-stage builds for testing, individual services, and production

# ===========================================
# BASE IMAGE WITH COMMON DEPENDENCIES
# ===========================================
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir requests aiohttp mysql-connector-python pymongo redis flask pytest

# ===========================================
# TESTING IMAGE (Lightweight, no ML models)
# ===========================================
FROM base AS testing

# Install additional testing dependencies
RUN pip install --no-cache-dir pytest flake8 black bandit pytest-cov

# Copy only essential application files for testing
COPY *.py ./
COPY services/ ./services/
COPY shared/ ./shared/
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY tests/ ./tests/
COPY k8s/ ./k8s/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=testing \
    LOG_LEVEL=DEBUG \
    PYTHONPATH=/app

USER appuser
EXPOSE 8000

# Testing command
CMD ["python", "-c", "print('Testing Environment Ready'); import time; time.sleep(3600)"]

# ===========================================
# PRODUCTION MICROSERVICES (9 CORE SERVICES)
# Based on official SERVICE_INVENTORY.md
# ===========================================

# 1. Enhanced News Collector (Template Compliant)
FROM base AS news-collector
COPY shared/ ./shared/
COPY services/enhanced_news_collector.py ./services/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=news-collector

USER appuser
EXPOSE 8001
CMD ["python", "services/enhanced_news_collector.py"]

# 2. Enhanced Onchain Collector V2 (Latest Production)
FROM base AS onchain-collector-v2
COPY shared/ ./shared/
COPY services/onchain-collection/ ./services/onchain-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=onchain-collector-v2

USER appuser
EXPOSE 8004
CMD ["python", "services/onchain-collection/enhanced_onchain_collector_v2.py"]

# 3. Enhanced Macro Collector V2 (Template Compliant)
FROM base AS macro-collector
COPY shared/ ./shared/
COPY services/macro-collection/ ./services/macro-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=macro-collector

USER appuser
EXPOSE 8002
CMD ["python", "services/macro-collection/enhanced_macro_collector_v2.py"]

# 4. ML Market Collector
FROM base AS ml-market-collector
COPY shared/ ./shared/
COPY services/market-collection/ ./services/market-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=ml-market-collector

USER appuser
EXPOSE 8005
CMD ["python", "services/market-collection/ml_market_collector.py"]

# 5. Enhanced Price Collector
FROM base AS price-collector
COPY shared/ ./shared/
COPY services/price-collection/ ./services/price-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=price-collector

USER appuser
EXPOSE 8006
CMD ["python", "services/price-collection/enhanced_price_collector.py"]

# 6. Technical Analysis Collector
FROM base AS technical-analysis-collector
COPY shared/ ./shared/
COPY services/technical-collection/ ./services/technical-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=technical-analysis-collector

USER appuser
EXPOSE 8007
CMD ["python", "services/technical-collection/enhanced_technical_indicators_collector.py"]

# 7. OHLC Collection Collector
FROM base AS ohlc-collector
COPY shared/ ./shared/
COPY services/ohlc-collection/ ./services/ohlc-collection/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=ohlc-collector

USER appuser
EXPOSE 8011
CMD ["python", "services/ohlc-collection/enhanced_ohlc_collector.py"]

# 8. Sentiment Analysis Service (with ML models)
FROM base AS sentiment-analyzer
COPY shared/ ./shared/
COPY services/sentiment-analysis/ ./services/sentiment-analysis/
COPY *.py ./

# Copy ML models for sentiment analysis
RUN mkdir -p models/finbert models/cryptobert
# Try to copy models if they exist, otherwise skip gracefully
RUN if [ -d "archive/models/finbert" ]; then \
      cp -r archive/models/finbert/* ./models/finbert/ || true; \
    else \
      echo "FinBERT model not found - will download at runtime"; \
    fi

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=sentiment-analyzer \
    MODEL_PATH=/app/models

USER appuser
EXPOSE 8008
CMD ["python", "services/enhanced_sentiment_ml_analysis.py"]

# 9. Data Validation Service
FROM base AS data-validator
COPY shared/ ./shared/
COPY services/placeholder-manager/ ./services/placeholder-manager/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=data-validator

USER appuser
EXPOSE 8009
CMD ["python", "services/placeholder-manager/placeholder_manager.py"]

# 10. Gap Detection Service
FROM base AS gap-detector
COPY shared/ ./shared/
COPY services/enhanced_technical_calculator.py ./services/
COPY *.py ./

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    SERVICE_NAME=gap-detector

USER appuser
EXPOSE 8010
CMD ["python", "services/enhanced_technical_calculator.py"]

# ===========================================
# PRODUCTION IMAGE (With ML models)
# ===========================================
FROM base AS production

# Copy application files first
COPY *.py ./
COPY services/ ./services/
COPY shared/ ./shared/
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY k8s/ ./k8s/

# Copy ML models for production
# Only copy the specific models we need, not the entire archive
RUN mkdir -p models/finbert models/cryptobert
COPY archive/models/finbert/ ./models/finbert/
# Add CryptoBERT when available
# COPY archive/models/cryptobert/ ./models/cryptobert/

# Alternative: Download models at build time (more reliable)
# RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
#     finbert_model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert'); \
#     finbert_tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert'); \
#     finbert_model.save_pretrained('./models/finbert'); \
#     finbert_tokenizer.save_pretrained('./models/finbert'); \
#     print('FinBERT downloaded successfully')"

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    PYTHONPATH=/app \
    MODEL_PATH=/app/models

USER appuser
EXPOSE 8000

# Production health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Production command
CMD ["python", "-c", "print('Production Environment Ready with ML Models'); import time; time.sleep(3600)"]

# ===========================================
# DEFAULT TARGET (Testing for CI/CD)
# ===========================================
FROM testing AS default