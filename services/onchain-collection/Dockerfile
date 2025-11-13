FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY services/onchain-collection/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the enhanced onchain collector and shared modules
COPY services/onchain-collection/enhanced_onchain_collector.py .
COPY shared/ ./shared/

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV SERVICE_NAME=enhanced-onchain-collector

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the enhanced onchain collector
CMD ["python", "enhanced_onchain_collector.py"]