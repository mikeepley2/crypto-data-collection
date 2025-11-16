# Crypto Data Collection System - Dockerfile
# Multi-stage build for efficient container images

# ==========================================
# BASE IMAGE WITH PYTHON DEPENDENCIES
# ==========================================
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt* ./
COPY setup.py* ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 2>/dev/null || \
    pip install --no-cache-dir requests aiohttp mysql-connector-python pymongo redis

# ==========================================
# DEVELOPMENT IMAGE
# ==========================================
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir pytest flake8 black isort bandit

# Copy source code
COPY . .

# Set development environment
ENV ENVIRONMENT=development
ENV LOG_LEVEL=DEBUG

# Expose common ports
EXPOSE 8000 8001 8002 8003 8004 8005 8006

# Default command for development
CMD ["python", "-m", "uvicorn", "src.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==========================================
# PRODUCTION IMAGE
# ==========================================
FROM base as production

# Copy only necessary files
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY k8s/ ./k8s/

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set production environment
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose default port
EXPOSE 8000

# Default command for production
CMD ["python", "-m", "uvicorn", "src.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==========================================
# SPECIALIZED SERVICE IMAGES
# ==========================================

# Price Collection Service
FROM base as price-collector
COPY src/services/price_collection/ ./src/services/price_collection/
COPY src/shared/ ./src/shared/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["python", "src/services/price_collection/enhanced_crypto_prices_collector.py"]

# News Collection Service  
FROM base as news-collector
COPY src/services/news_collection/ ./src/services/news_collection/
COPY src/shared/ ./src/shared/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8001
CMD ["python", "src/services/news_collection/crypto_news_collector.py"]

# Sentiment Analysis Service
FROM base as sentiment-analyzer
COPY src/services/sentiment_analysis/ ./src/services/sentiment_analysis/
COPY src/shared/ ./src/shared/
RUN pip install --no-cache-dir transformers torch
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8002
CMD ["python", "src/services/sentiment_analysis/sentiment_collector.py"]

# Technical Indicators Service
FROM base as technical-indicators
COPY src/services/technical_analysis/ ./src/services/technical_analysis/
COPY src/shared/ ./src/shared/
RUN pip install --no-cache-dir ta-lib numpy pandas
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8003
CMD ["python", "src/services/technical_analysis/technical_indicators_collector.py"]

# Materialized Updater Service
FROM base as materialized-updater
COPY src/docker/materialized_updater/ ./src/docker/materialized_updater/
COPY src/shared/ ./src/shared/
RUN chown -R appuser:appuser /app
USER appuser
CMD ["python", "src/docker/materialized_updater/realtime_materialized_updater.py"]