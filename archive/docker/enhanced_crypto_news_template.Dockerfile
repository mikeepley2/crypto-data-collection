# Template-Compliant Enhanced Crypto News Collector Dockerfile
FROM python:3.11-slim

LABEL maintainer="crypto-data-team"
LABEL version="template-compliant-1.0"
LABEL description="Enhanced Crypto News Collector implementing standardized collector template"

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r collector && useradd -r -g collector collector

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY templates/collector_template/ ./templates/collector_template/
COPY services/enhanced_news_collector_template.py ./services/
COPY schemas/ ./schemas/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/schemas && \
    chown -R collector:collector /app

# Copy health check script
COPY <<EOF /app/healthcheck.py
import sys
import aiohttp
import asyncio

async def check_health():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8000/health', timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
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
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=enhanced-crypto-news

# Run the collector
CMD ["python", "/app/services/enhanced_news_collector_template.py"]