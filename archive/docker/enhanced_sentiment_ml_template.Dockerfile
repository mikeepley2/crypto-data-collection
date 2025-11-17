# Template-Compliant Enhanced ML Sentiment Collector Dockerfile
FROM python:3.11-slim

LABEL maintainer="crypto-data-team"
LABEL version="template-compliant-1.0"
LABEL description="Enhanced ML Sentiment Collector implementing standardized collector template with PyTorch and Transformers"

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r collector && useradd -r -g collector collector

# Install system dependencies including ML libraries
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models to reduce startup time (optional)
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='kk08/CryptoBERT', device=-1)" || true
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='ProsusAI/finbert', device=-1)" || true

# Copy source code
COPY templates/collector_template/ ./templates/collector_template/
COPY services/enhanced_sentiment_ml_template.py ./services/
COPY schemas/ ./schemas/

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/schemas /root/.cache/huggingface && \
    chown -R collector:collector /app

# Copy health check script
COPY <<EOF /app/healthcheck.py
import sys
import aiohttp
import asyncio

async def check_health():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health', timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") in ["healthy", "degraded"]:
                        print("Health check passed")
                        return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

if __name__ == "__main__":
    result = asyncio.run(check_health())
    sys.exit(0 if result else 1)
EOF

# Make healthcheck script executable
RUN chmod +x /app/healthcheck.py

# Switch to non-root user
USER collector

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python /app/healthcheck.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=enhanced-sentiment-ml
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV HF_HOME=/root/.cache/huggingface

# Run the collector
CMD ["python", "/app/services/enhanced_sentiment_ml_template.py"]